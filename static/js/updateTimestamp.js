function updateTimestamp() {
    var now = new Date();
    document.getElementById("timestamp").innerText = `Last checked: ${now.toLocaleString()}`;
}