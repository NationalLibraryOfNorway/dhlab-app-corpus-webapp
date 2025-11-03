/*
    Some fields for the corpus definition form are only allowed for the "digibok" document type.
    This functions adds an event listener to the document type dropdown to ensure that "illegal" fields are disabled
    whenever the document type changes.
*/
let languageSelector;

function autoupdateAllowedCorpusSearchFields() {
    let docTypeSelection = document.getElementById('doc-type-selection');
    function updateAllowedFields() {
        let authorField = document.getElementById('author-input');
        let subjectField = document.getElementById('subject-input');
        let deweyField = document.getElementById('dewey-input')
        let wordsPhrasesField = document.getElementById('words-or-phrases-input')

        if (docTypeSelection.value === 'digibok') {
            authorField.disabled = false;
            deweyField.disabled = false;
            subjectField.disabled = false;

        } else {
            authorField.disabled = true;
            authorField.value = "";
            deweyField.disabled = true;
            deweyField.value = "";
            subjectField.disabled = true;
            subjectField.value = "";
        }

        if (docTypeSelection.value == 'digavis') {
            if (languageSelector){
                languageSelector.selectedItems.map((value) => languageSelector.unselect(value.value))
                languageSelector.disable();
            }
        } else {
            if (languageSelector)
                languageSelector.enable();
        }


    }

    docTypeSelection.addEventListener('change', updateAllowedFields);
    updateAllowedFields();
}
