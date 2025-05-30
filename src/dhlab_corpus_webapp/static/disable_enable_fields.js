document.addEventListener("click", function() {
    var docTypeSelection = document.getElementById('doc_type_selection_');
    //if (!docTypeSelection) {
    //    console.error("Dropdown not found");
    //    return; 
    //}
    
    var authorField = document.getElementById('author_');
    var deweyField = document.getElementById('dewey_')

    var authorOriginalPlaceholder = authorField.placeholder || "Henrik Ibsen";
    var deweyOriginalPlaceholder = deweyField.placeholder || "";

    function updateAuthorField() {
        console.log("Dropdown value changed to:", docTypeSelection.value); 

        if (docTypeSelection.value === 'digibok') {
            console.log("Enabling author field for Digibok");
            authorField.readOnly =false; //endret fra "disabled" for å unngå rødt stoppskilt
            deweyField.readOnly=false;
            authorField.placeholder = authorOriginalPlaceholder;
            deweyField.placeholder = deweyOriginalPlaceholder;

        } else {
            authorField.readOnly=true;
            deweyField.readOnly=true;
            authorField.placeholder = "Kan ikke velges";
            deweyField.placeholder = "Kan ikke velges";

        }
    }

    docTypeSelection.addEventListener('change', updateAuthorField);

    updateAuthorField();
});
