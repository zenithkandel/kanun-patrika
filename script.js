for (let i = 1; i <= 217; i++) {
    const element = document.querySelector(`body > div.entry > table > tbody > tr:nth-child(${i}) > td:nth-child(6) > a`);
    element.setAttribute("download", i);
    // element.click();
}