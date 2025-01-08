document.addEventListener("DOMContentLoaded", function() {
    var docTypeSelection = document.getElementById('doc_type_selection_');
    if (!docTypeSelection) {
        console.error("Dropdown not found");
        return; 
    }
    
    var authorField = document.getElementById('author');
    var deweyField = document.getElementById('dewey')

    function updateAuthorField() {
        console.log("Dropdown value changed to:", docTypeSelection.value); 

        if (docTypeSelection.value === 'digibok') {
            console.log("Enabling author field for Digibok");
            authorField.disabled =false;
            deweyField.disabled=false;

        } else {
            authorField.disabled=true;
            deweyField.disabled=true;

        }
    }

    docTypeSelection.addEventListener('change', updateAuthorField);

    updateAuthorField();
});
