function networkSettings() {
    $('#loadingSpinner').show();
    updateTimestamp();

    var selectedDevice = document.getElementById("deviceDropdown").value;
    $.ajax({
        url: '/api/network_settings/' + selectedDevice,
        type: 'GET',
        success: function(response) {
            $('#loadingSpinner').hide();
            var outputDiv = document.getElementById("output");
            outputDiv.innerHTML = `<div class="card">
                <div class="card-header">
                    Network Settings - Device ${response.client_id}
                </div>
                <div class="card-body">
                    <p><strong>Status:</strong> ${response.status}</p>
                    <p><strong>Hostname:</strong> ${response.hostname}</p>
                    <p><strong>IP Address:</strong> ${response.ip_address}</p>
                    <p><strong>MAC Address:</strong> ${response.mac_address}</p>
                    <p><strong>WiFi SSID:</strong> ${response.wifi_ssid}</p>
                </div>
            </div>`;
        },
        error: displayError
    });
}