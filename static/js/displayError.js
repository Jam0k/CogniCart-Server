function displayError(xhr, status, error) {
    $('#loadingSpinner').hide();
    document.getElementById("output").innerHTML = "<div class='alert alert-danger'>Failed to get data</div>";
}