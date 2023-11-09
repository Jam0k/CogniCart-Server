function takePhoto() {
    const deviceDropdown = document.getElementById("deviceDropdown");
    const deviceId = deviceDropdown.value;

    $("#loadingSpinner").show(); // Show the spinner

    fetch(`/api/take_photo/${deviceId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json(); // Convert the response data to JSON
        })
        .then(data => {
            console.log(data); // Log the response data for debugging

            // Check if the photo data is present
            if (!data.photo) {
                throw new Error('No photo data found');
            }

            // Convert base64 to a blob
            const byteCharacters = atob(data.photo);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: 'image/jpeg' });

            // Hide the spinner
            $("#loadingSpinner").hide();

            const url = window.URL.createObjectURL(blob);
            const image = document.getElementById("photoDisplay");
            image.src = url;
            image.onload = () => {
                window.URL.revokeObjectURL(url); // Revoke the Blob URL once the image is loaded
            };
            image.style.display = "block"; // Display the image
        })
        .catch(error => {
            // Hide the spinner
            $("#loadingSpinner").hide();
            
            console.error("Error taking photo:", error);
        });
}
