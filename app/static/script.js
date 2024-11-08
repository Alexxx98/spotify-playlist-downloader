function downloadFile(event, author, filename) {
    const downloadBtn = event.target;
    const convertCircle = event.target.nextElementSibling;

    downloadBtn.style.display = 'none';
    convertCircle.style.display = 'block';

    console.log(event)
    console.log(event.target.nextElementSibling)
    fetch(`/download/${author}${filename}`)
        .then(response => {
            if (!response.ok) {
                downloadBtn.style.display = 'block';
                convertCircle.style.display = 'none';
                throw new Error("Bad response from the server.")
            }
            return response.blob();
        })
        .then(blob => {
            // Create url and a tag for the song to donwload
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');

            // Hide the a tag and assign the url to it
            a.style.display = 'none';
            a.href = url;

            // Set the name of the file to download
            a.download = `${author}-${filename}.wav`;

            // Add the a tag to DOM
            document.body.appendChild(a);

            // Click the a tag to download and remove it with the url
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        })
        .catch(error => console.error('Download failed:', error));

}