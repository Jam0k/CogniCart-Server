function generateImage() {
    const deviceDropdown = document.getElementById('deviceDropdown');
    const selectedDevice = deviceDropdown.value;
    
    $("#loadingSpinner").show(); // Show the spinner

    $.ajax({
        url: `/api/take_photos_all`, // The correct API endpoint
        type: 'GET',
        success: function(photosData) {
            // Hide the spinner
            $("#loadingSpinner").hide();

            const imageDisplayArea = document.getElementById('imageDisplayArea');
            imageDisplayArea.innerHTML = ''; // Clear the area

            // Iterate over the array of photo data objects
            photosData.forEach(photoData => {
                // Create a container div for each image and client ID
                const imageContainer = document.createElement('div');
                imageContainer.classList.add('col-md-4', 'text-center', 'mb-4'); // Bootstrap classes

                // Check if there is an error key in the object
                if (photoData.error) {
                    console.error('Error for client:', photoData.client_id, photoData.error);
                    // Add an error message to the imageContainer
                    const errorDiv = document.createElement('div');
                    errorDiv.textContent = `Error for client ${photoData.client_id}: ${photoData.error}`;
                    imageContainer.appendChild(errorDiv);
                } else {
                    // Create a paragraph element for the client ID
                    const clientIdParagraph = document.createElement('p');
                    clientIdParagraph.textContent = photoData.client_id;
                    clientIdParagraph.classList.add('client-id'); // Add class for styling if needed

                    // Create an image element for the base64 image string
                    const img = document.createElement('img');
                    img.src = 'data:image/jpeg;base64,' + photoData.photo; // Set the src to the base64 string
                    img.style.maxWidth = '100%';
                    img.alt = `Image for ${photoData.client_id}`; // Accessibility improvement
                    
                    // Append the client ID and image to the imageContainer
                    imageContainer.appendChild(clientIdParagraph);
                    imageContainer.appendChild(img);
                }

                // Add the imageContainer to the display area
                imageDisplayArea.appendChild(imageContainer);
            });
        },
        error: function(error) {
            // Hide the spinner
            $("#loadingSpinner").hide();
            
            console.error('Error generating images:', error);
        }
    });
}
