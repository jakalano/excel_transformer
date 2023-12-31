console.log("main.js loaded");
document.addEventListener("DOMContentLoaded", function () {

    function handleDeleteFile() {
        let deleteFileBtn = document.getElementById('deleteFileBtn');
        if (deleteFileBtn) {
            deleteFileBtn.addEventListener('click', function() {
                if (confirm('Are you sure you want to delete this file?')) {
                    let deleteUrl = deleteFileBtn.getAttribute('data-url');
                    let csrfToken = deleteFileBtn.getAttribute('data-csrf');

                    fetch(deleteUrl, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ 'delete': true })
                    }).then(function(response) {
                        if (response.ok) {
                            window.location.href = '/';
                        } else {
                            alert('Error: Unable to delete the file.');
                        }
                    });
                }
            });
        }
    }

    handleDeleteFile();


    function handleDeleteTemplate() {
        let deleteTemplateBtns = document.querySelectorAll('.deleteTemplateBtn');
        deleteTemplateBtns.forEach(button => {
            button.addEventListener('click', function() {
                if (confirm('Are you sure you want to delete this template?')) {
                    let deleteUrl = button.getAttribute('data-url');
                    let csrfToken = button.getAttribute('data-csrf');

                    fetch(deleteUrl, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': csrfToken,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ 'delete': true })
                    }).then(function(response) {
                        if (response.ok) {
                            // Optionally, remove the template from the UI or refresh the page
                            button.closest('.accordion-item').remove();
                        } else {
                            alert('Error: Unable to delete the template.');
                        }
                    });
                }
            });
        });
    }

    handleDeleteTemplate();

    
  function handleSummaryPageActions() {
    // check if you're on the summary pages
    if (window.location.pathname === "/summary/") {
      //
      console.log("Summary page");
      let nextPageLink = document.querySelector(
        '.page-link[href="/edit_data/"]'
      );
      let removeRowsCheckbox = document.getElementById("removeRowsCheckbox");
      let removeColsCheckbox = document.getElementById("removeColsCheckbox");
      let removeEmptyRowsForm = document.getElementById("removeEmptyRowsForm");
      if (removeRowsCheckbox || removeColsCheckbox) {
        console.log("checkbox");
        if (nextPageLink) {
          console.log("Next page link found", nextPageLink);
          nextPageLink.addEventListener("click", function (event) {
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
      let addNewColumnBtn = document.getElementById("addNewColumnBtn");
      if (addNewColumnBtn) {
        addNewColumnBtn.addEventListener("click", function (event) {
          event.preventDefault(); // Prevent default button behavior

          let newInputDiv = document.createElement("div");
          newInputDiv.classList.add("mb-2");

          let newInput = document.createElement("input");
          newInput.type = "text";
          newInput.name = "new_column[]";
          newInput.placeholder = "New Column Name";
          newInput.classList.add("form-control"); // Apply Bootstrap styling

          newInputDiv.appendChild(newInput);
          document
            .getElementById("newColumnsContainer")
            .appendChild(newInputDiv);
        });
      }
    }
  }
    handleSummaryPageActions();
    
  

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

  ///////////// undo functionality /////////////
  // let undoButton = document.getElementById("undo-button");
  // if (undoButton) {
  //   undoButton.addEventListener("click", async function (event) {
  //     event.preventDefault();
  //     console.log("Undo button clicked!");

  //     try {
  //       let response = await fetch("/undo/", {
  //         method: "POST",
  //         headers: {
  //           "Content-Type": "application/json",
  //           "X-CSRFToken": csrfToken,
  //         },
  //         body: JSON.stringify({
  //           session_key: sessionKey,
  //         }),
  //       });
  //       let text = await response.text();

  //       console.log(text);

  //       if (!response.ok) {
  //         throw new Error(
  //           "Network response was not ok: " + response.statusText
  //         );
  //       }

  //       let data = await response.json();
  //       if (data.status === "success") {
  //         // Update the table with the new HTML
  //         document.getElementById("summary-table").innerHTML =
  //           data.updated_table;
  //       } else {
  //         console.error("Error from server:", data.error);
  //       }
  //     } catch (error) {
  //       console.error(
  //         "There was a problem with the fetch operation:",
  //         error.message
  //       );
  //     }
  //   });
  // } else {
  //   console.error("Undo button not found!");
  // }

  //////////// undo table autorefresh V2 :(

  /*
    ///////////// undo functionality /////////////
    let undoButton = document.getElementById('undo-button');
    if (undoButton) {
        undoButton.addEventListener('click', async function(event) {
            event.preventDefault();
            console.log("Undo button clicked!");

            // Get the current view from the URL
            let currentView = window.location.pathname.split('/').pop();

            try {
                let undoUrl = '/undo/?current_view=' + currentView; // Append current view to the undo URL

                let response = await fetch(undoUrl, {  // Use the new undoUrl with the query parameter
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken,
                    },
                    body: JSON.stringify({
                        'session_key': sessionKey,
                    })
                });

                if(!response.ok) {
                    throw new Error('Network response was not ok: ' + response.statusText);
                }

                let data = await response.json();
                if (data.status === 'success') {
                    // Update the table with the new HTML
                    document.getElementById('summary-table').innerHTML = data.updated_table;
                } else {
                    console.error('Error from server:', data.error);
                }
            } catch(error) {
                console.error('There was a problem with the fetch operation:', error.message);
            }
        });
    } else {
        console.error('Undo button not found!');
    }


    */

  ///////////// regex text field appears only when regex selected in edit_data /////////////

  var validationTypeSelect = document.getElementById("validation_type");
  if (validationTypeSelect) {
    var regexInput = document.getElementById("regex_pattern");

    // function to show/hide regex input
    function toggleRegexInput() {
      if (validationTypeSelect.value === "regex") {
        regexInput.style.display = "block";
      } else {
        regexInput.style.display = "none";
      }
    }

    // event listener for change on validation type dropdown
    validationTypeSelect.addEventListener("change", toggleRegexInput);

    // initial check in case of page reload
    toggleRegexInput();
  }
  /////////////// JavaScript for handling duplicates ///////////

  function renderDuplicates(duplicates) {
    let table = document.getElementById("duplicates-table");
    let thead = table.createTHead();
    let tbody = table.createTBody();

    tbody.setAttribute("id", "duplicates-tbody");
    thead.innerHTML = "";
    tbody.innerHTML = "";

    // creates headers
    let row = thead.insertRow();
    if (duplicates.length > 0) {
      Object.keys(duplicates[0]).forEach((key) => {
        let th = document.createElement("th");
        th.textContent = key;
        row.appendChild(th);
      });
    }

    duplicates.forEach((row, index) => {
      let tr = document.createElement("tr");
      Object.values(row).forEach((value) => {
        let td = document.createElement("td");
        td.textContent = value;
        tr.appendChild(td);
      });
      // Add a checkbox for selecting the row
      let selectTd = document.createElement("td");
      let checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.classList.add("duplicate-checkbox");
      checkbox.dataset.rowIndex = index; // Keep track of the row index
      selectTd.appendChild(checkbox);
      tr.appendChild(selectTd);

      tbody.appendChild(tr);
    });
  }

  // checks if showing duplicates
  if ("{{ showing_duplicates }}") {
    try {
      let duplicates = JSON.parse("{{ request.session.duplicates|escapejs }}");
      renderDuplicates(duplicates);
    } catch (error) {
      console.error("Error parsing duplicates JSON:", error);
    }
  }

  // handle deletion of selected duplicates
  function deleteSelected() {
    let checkboxes = document.querySelectorAll(".duplicate-checkbox");
    let selectedIndices = Array.from(checkboxes)
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.dataset.rowIndex);

    let form = document.getElementById("delete-duplicates-form");
    let input = document.createElement("input");
    input.type = "hidden";
    input.name = "selected_rows";
    input.value = JSON.stringify(selectedIndices);
    form.appendChild(input);
    form.submit();
  }

  // adds event listener to your delete button
  let deleteButton = document.getElementById("delete-duplicates-button");
  if (deleteButton) {
    deleteButton.addEventListener("click", deleteSelected);
  }
});
