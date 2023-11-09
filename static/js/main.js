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

    ///////////// undo functionality /////////////
    let undoButton = document.getElementById('undo-button');
    if (undoButton) {
        undoButton.addEventListener('click', async function(event) {
            // Prevent form submission
            event.preventDefault();
            console.log("Undo button clicked!");

            // Initialize responseClone outside of the try block
            let responseClone;

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

                // Clone the response right after fetching
                responseClone = response.clone();

                if(!response.ok) {
                    throw new Error('Network response was not ok: ' + response.statusText);
                }

                let data = await response.json();
                // Handle your data...
            } catch(error) {
                console.error('There was a problem with the fetch operation:', error.message);
                // Use the cloned response to read the text without consuming the original response
                if(responseClone) {
                    responseClone.text().then(text => console.error('Response text:', text));
                } else {
                    console.error('Response clone is not available.');
                }
            }
        });
    } else {
        console.error('Undo button not found!');
    }



    ///////////// regex text field appears only when regex selected in edit_data /////////////

    var validationTypeSelect = document.getElementById('validation_type');
    var regexInput = document.getElementById('regex_pattern');

    // Function to show/hide regex input
    function toggleRegexInput() {
        if (validationTypeSelect.value === 'regex') {
            regexInput.style.display = 'block';
        } else {
            regexInput.style.display = 'none';
        }
    }

    // Event listener for change on validation type dropdown
    validationTypeSelect.addEventListener('change', toggleRegexInput);

    // Initial check in case of page reload
    toggleRegexInput();


    /////////////// JavaScript for handling duplicates ///////////
    

    
    function renderDuplicates(duplicates) {
        let table = document.getElementById('duplicates-table'); // Assume you have a table with this ID
        let thead = table.createTHead();
        let tbody = table.createTBody();
    
        tbody.setAttribute('id', 'duplicates-tbody');
        thead.innerHTML = '';
        tbody.innerHTML = '';
    
        // Create headers
        let row = thead.insertRow();
        if (duplicates.length > 0) {
            Object.keys(duplicates[0]).forEach(key => {
                let th = document.createElement('th');
                th.textContent = key;
                row.appendChild(th);
            });
        }

        duplicates.forEach((row, index) => {
            let tr = document.createElement('tr');
            Object.values(row).forEach(value => {
                let td = document.createElement('td');
                td.textContent = value;
                tr.appendChild(td);
            });
            // Add a checkbox for selecting the row
            let selectTd = document.createElement('td');
            let checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.classList.add('duplicate-checkbox');
            checkbox.dataset.rowIndex = index; // Keep track of the row index
            selectTd.appendChild(checkbox);
            tr.appendChild(selectTd);
            
            tbody.appendChild(tr);
        });
    }

    // Check if showing duplicates
    if ("{{ showing_duplicates }}") {
        let duplicates = JSON.parse('{{ request.session.duplicates|escapejs }}');
        renderDuplicates(duplicates);
    }

    // Function to handle deletion of selected duplicates
    function deleteSelected() {
        let checkboxes = document.querySelectorAll('.duplicate-checkbox');
        let selectedIndices = Array.from(checkboxes)
                                  .filter(checkbox => checkbox.checked)
                                  .map(checkbox => checkbox.dataset.rowIndex);
        
        // Assuming you have a form with an ID 'delete-duplicates-form'
        let form = document.getElementById('delete-duplicates-form');
        let input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'selected_rows';
        input.value = JSON.stringify(selectedIndices);
        form.appendChild(input);
        form.submit();
    }

    // Add event listener to your delete button
    let deleteButton = document.getElementById('delete-duplicates-button');
    if (deleteButton) {
        deleteButton.addEventListener('click', deleteSelected);
    }
        

        });
    







// Call the function when the document is ready
document.addEventListener('DOMContentLoaded', handleSummaryPageActions);

