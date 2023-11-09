function checkCamera() {
    const deviceDropdown = document.getElementById('deviceDropdown');
    const selectedDevice = deviceDropdown.value;
    
    $("#loadingSpinner").show(); // Show the spinner
    
    $.ajax({
        url: `/api/camera_check/${selectedDevice}`,
        type: 'GET',
        success: function(response) {
            // Hide the spinner
            $("#loadingSpinner").hide();
            
            // Displaying the result on the webpage
            document.getElementById('output').innerText = `Camera Status: ${response.camera_status}`;
        },
        error: function(error) {
            // Hide the spinner
            $("#loadingSpinner").hide();
            
            console.error(error);
        }
    });
}
