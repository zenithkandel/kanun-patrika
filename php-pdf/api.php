<?php
header('Content-Type: application/json');
header('Cache-Control: no-cache, no-store, must-revalidate');

$action = $_GET['action'] ?? 'status';
$dir = __DIR__;
$progressFile = "$dir/progress.json";
$urlsFile = dirname($dir) . '/urls.txt';
$downloadDir = "$dir/files";

switch ($action) {
    case 'start':
        startDownload($progressFile, $urlsFile, $downloadDir);
        break;
    case 'status':
        getStatus($progressFile);
        break;
    case 'cancel':
        cancelDownload($progressFile);
        break;
    case 'reset':
        resetDownload($progressFile);
        break;
    default:
        http_response_code(400);
        echo json_encode(['error' => 'Invalid action']);
}

/* ──────────────────────────── START ──────────────────────────── */

function startDownload($progressFile, $urlsFile, $downloadDir)
{
    if (!file_exists($urlsFile)) {
        http_response_code(404);
        echo json_encode(['error' => 'urls.txt not found at: ' . $urlsFile]);
        return;
    }

    if (file_exists($progressFile)) {
        $cur = @json_decode(file_get_contents($progressFile), true);
        if (is_array($cur) && ($cur['status'] ?? '') === 'running') {
            echo json_encode(['error' => 'Download already in progress']);
            return;
        }
    }

    set_time_limit(0);
    ignore_user_abort(true);

    $lines = file($urlsFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $urls  = array_values(array_filter(array_map('trim', $lines)));

    if (!is_dir($downloadDir)) {
        mkdir($downloadDir, 0755, true);
    }

    $state = [
        'status'     => 'running',
        'total'      => count($urls),
        'completed'  => 0,
        'downloaded' => 0,
        'skipped'    => 0,
        'failed'     => 0,
        'totalSize'  => 0,
        'startTime'  => microtime(true),
        'files'      => [],
    ];
    writeProgress($progressFile, $state);

    foreach (array_chunk($urls, 40) as $batch) {
        $check = @json_decode(file_get_contents($progressFile), true);
        if (!is_array($check) || ($check['status'] ?? '') !== 'running') {
            break;
        }
        downloadBatch($batch, $downloadDir, $progressFile);
    }

    $final = @json_decode(file_get_contents($progressFile), true);
    if (is_array($final) && ($final['status'] ?? '') === 'running') {
        $final['status'] = 'completed';
    }
    if (is_array($final)) {
        $final['duration'] = round(microtime(true) - $final['startTime'], 2);
        writeProgress($progressFile, $final);
        echo json_encode($final);
    }
}

/* ──────────────────────────── BATCH ──────────────────────────── */

function downloadBatch($urls, $downloadDir, $progressFile)
{
    $mh  = curl_multi_init();
    $map = [];

    foreach ($urls as $url) {
        $name = basename(parse_url($url, PHP_URL_PATH));
        $path = "$downloadDir/$name";

        if (file_exists($path) && filesize($path) > 0) {
            incrementProgress($progressFile, 'skipped', $name);
            continue;
        }

        $ch = curl_init($url);
        $fp = @fopen($path, 'w');

        if (!$fp) {
            curl_close($ch);
            incrementProgress($progressFile, 'failed', $name, 'Cannot write file');
            continue;
        }

        curl_setopt_array($ch, [
            CURLOPT_FILE           => $fp,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_TIMEOUT        => 60,
            CURLOPT_CONNECTTIMEOUT => 10,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_USERAGENT      => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        ]);

        $map[(int) $ch] = [
            'ch'   => $ch,
            'fp'   => $fp,
            'file' => $name,
            'path' => $path,
            'url'  => $url,
        ];
        curl_multi_add_handle($mh, $ch);
    }

    if (empty($map)) {
        curl_multi_close($mh);
        return;
    }

    do {
        $status = curl_multi_exec($mh, $active);

        while ($info = curl_multi_info_read($mh)) {
            if ($info['msg'] !== CURLMSG_DONE) {
                continue;
            }

            $key = (int) $info['handle'];
            if (!isset($map[$key])) {
                continue;
            }

            $h    = $map[$key];
            $code = curl_getinfo($h['ch'], CURLINFO_HTTP_CODE);
            $err  = curl_error($h['ch']);
            $ok   = ($info['result'] === CURLE_OK
                     && $code === 200
                     && file_exists($h['path'])
                     && filesize($h['path']) > 0);

            if ($ok) {
                $check = @fopen($h['path'], 'r');
                $hdr   = $check ? fread($check, 4) : '';
                if ($check) fclose($check);
                $ok = ($hdr === '%PDF');
            }

            fclose($h['fp']);
            curl_multi_remove_handle($mh, $h['ch']);
            curl_close($h['ch']);

            if ($ok) {
                $size = filesize($h['path']);
                incrementProgress($progressFile, 'downloaded', $h['file'], null, $size);
            } else {
                @unlink($h['path']);
                $reason = $err ?: ($code !== 200 ? "HTTP $code" : 'Invalid PDF');
                incrementProgress($progressFile, 'failed', $h['file'], $reason);
            }

            unset($map[$key]);
        }

        if ($active) {
            curl_multi_select($mh, 0.1);
        }
    } while ($active && $status === CURLM_OK);

    foreach ($map as $h) {
        @fclose($h['fp']);
        @curl_multi_remove_handle($mh, $h['ch']);
        @curl_close($h['ch']);
        @unlink($h['path']);
        incrementProgress($progressFile, 'failed', $h['file'], 'Connection failed');
    }

    curl_multi_close($mh);
}

/* ──────────────────────────── HELPERS ──────────────────────────── */

function incrementProgress($progressFile, $type, $name, $error = null, $size = 0)
{
    $s = @json_decode(file_get_contents($progressFile), true);
    if (!is_array($s)) return;

    $s['completed']++;
    $s['files'][] = array_filter([
        'name'   => $name,
        'status' => $type,
        'error'  => $error,
        'size'   => $size,
    ], fn($v) => $v !== null);

    if ($type === 'downloaded') {
        $s['downloaded']++;
        $s['totalSize'] = ($s['totalSize'] ?? 0) + $size;
    } elseif ($type === 'failed') {
        $s['failed']++;
    } elseif ($type === 'skipped') {
        $s['skipped']++;
    }

    writeProgress($progressFile, $s);
}

function writeProgress($file, $data)
{
    $fp = @fopen($file, 'c');
    if (!$fp) return;
    flock($fp, LOCK_EX);
    ftruncate($fp, 0);
    fwrite($fp, json_encode($data));
    fflush($fp);
    flock($fp, LOCK_UN);
    fclose($fp);
}

function getStatus($progressFile)
{
    if (!file_exists($progressFile)) {
        echo json_encode(['status' => 'idle']);
        return;
    }
    $d = @json_decode(file_get_contents($progressFile), true);
    echo json_encode(is_array($d) ? $d : ['status' => 'idle']);
}

function cancelDownload($progressFile)
{
    if (file_exists($progressFile)) {
        $s = @json_decode(file_get_contents($progressFile), true);
        if (is_array($s)) {
            $s['status'] = 'cancelled';
            writeProgress($progressFile, $s);
        }
    }
    echo json_encode(['status' => 'cancelled']);
}

function resetDownload($progressFile)
{
    if (file_exists($progressFile)) {
        @unlink($progressFile);
    }
    echo json_encode(['status' => 'reset']);
}
