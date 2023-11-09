function ntpCheck() {
    $('#loadingSpinner').show();
    updateTimestamp();

    var selectedDevice = document.getElementById("deviceDropdown").value;
    $.ajax({
        url: '/api/ntp_check/' + selectedDevice,
        type: 'GET',
        success: function(response) {
            $('#loadingSpinner').hide();
            var outputDiv = document.getElementById("output");
            outputDiv.innerHTML = `<div class="card">
                <div class="card-header">
                    NTP Check - Device ${response.client_id}
                </div>
                <div class="card-body">
                    <p><strong>Status:</strong> <span class="${response.status === 'Online' ? 'text-success' : 'text-danger'}">${response.status}</span></p>
                    <p><strong>Current NTP Time:</strong> ${response.current_ntp_time}</p>
                </div>
            </div>`;
        },
        error: displayError
    });
}