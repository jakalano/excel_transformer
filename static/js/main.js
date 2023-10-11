console.log('main.js loaded');
function handleSummaryPageActions() {
    // Check if you're on the summary page
    if (window.location.pathname === '/summary/') { // Adjust this path according to your Django URL configuration for the summary page
        console.log("Summary page");
        let nextPageLink = document.querySelector('.page-link[href="/edit_data/"]');
        let removeRowsCheckbox = document.getElementById('removeRowsCheckbox');
        let removeColsCheckbox = document.getElementById('removeColsCheckbox');
        let removeEmptyRowsForm = document.getElementById('removeEmptyRowsForm');
        if (removeRowsCheckbox || removeColsCheckbox) {
            console.log("checkbox")
            if (nextPageLink) {
                console.log("Next page link found", nextPageLink);
                nextPageLink.addEventListener('click', function(event) {
                    console.log("Next page link clicked");
                    if (removeRowsCheckbox.checked || removeColsCheckbox.checked) {
                        event.preventDefault();
                        console.log("Checkbox is checked, submitting form");
                        removeEmptyRowsForm.submit();
                    }
                });
            } else {
                console.log("Next page link NOT found");
            }
            }
    }
}

// document.addEventListener('DOMContentLoaded', function() {
//     let undoButton = document.getElementById('undo-button');
//     if (undoButton) {
//         undoButton.addEventListener('click', function() {
//             console.log("Undo button clicked!");
//     // Send AJAX request to undo view
//     fetch('/undo/', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//             'X-CSRFToken': csrfToken,  // Pass CSRF token
//         },
//         body: JSON.stringify({
//             'session_key': sessionKey,
//         })
//     })
//     .then(response => response.json())
//     .then(data => {
//         // Update UI accordingly
//     })
// });
// } else {
//     console.error('Undo button not found!');
// }
// });

document.addEventListener('DOMContentLoaded', function() {
    let undoButton = document.getElementById('undo-button');
    if (undoButton) {
        undoButton.addEventListener('click', async function(event) {
            // Prevent form submission
            event.preventDefault();
            console.log("Undo button clicked!");

            try {
                let response = await fetch('/undo/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({
                        'session_key': sessionKey,
                    })
                });

                // Check if response is ok (status 200-299)
                if(!response.ok) {
                    throw new Error('Network response was not ok' + response.statusText);
                }

                let data = await response.json();
                // handle your data...
            } catch(error) {
                console.error('There was a problem with the fetch operation:', error);
            }
        });
    } else {
        console.error('Undo button not found!');
    }
});



// Call the function when the document is ready
document.addEventListener('DOMContentLoaded', handleSummaryPageActions);

