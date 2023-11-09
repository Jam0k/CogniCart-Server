function checkHealth() {
    $('#loadingSpinner').show();
    updateTimestamp();

    var selectedDevice = document.getElementById("deviceDropdown").value;
    $.ajax({
        url: '/api/health/' + selectedDevice,
        type: 'GET',
        success: function(response) {
            $('#loadingSpinner').hide();
            var outputDiv = document.getElementById("output");
            outputDiv.innerHTML = `<div class="card">
                <div class="card-header">
                    Health Check - Device ${response.client_id}
                </div>
                <div class="card-body">
                    <p><strong>Status:</strong> <span class="${response.status === 'Online' ? 'text-success' : 'text-danger'}">${response.status}</span></p>
                    <p><strong>CPU Usage:</strong> ${response.cpu_usage}</p>
                    <p><strong>Memory Usage:</strong> ${response.memory_usage}</p>
                    <p><strong>Disk Usage:</strong> ${response.disk_usage}</p>
                </div>
            </div>`;
        },
        error: displayError
    });
}
