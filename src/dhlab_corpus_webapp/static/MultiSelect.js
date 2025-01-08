const dropdownToggle = document.querySelector('.dropdown-toggle');
const dropdownMenu = document.querySelector('.dropdown');
const checkboxes = document.querySelectorAll('.checkbox');
const selectedTagsContainer = document.getElementById('selectedTags');
const hiddenFieldsContainer = document.getElementById('hidden-fields-container');
const langContainer = document.getElementById('langContainer'); 

function updateTags() {
    const selectedTags = [];

    checkboxes.forEach(checkbox => {
        if (checkbox.checked) {
            selectedTags.push(checkbox.value);
        }
    });

    selectedTagsContainer.innerHTML = '';  

    selectedTags.forEach(tag => {
        const tagElement = document.createElement('div');
        tagElement.classList.add('tag');
        tagElement.textContent = tag;

        const deleteSpan = document.createElement('span');
        deleteSpan.textContent = '×';
        deleteSpan.addEventListener('click', function () {
            removeTag(tag);
        });

        tagElement.appendChild(deleteSpan);
        selectedTagsContainer.appendChild(tagElement);
    });

    updateLangString(selectedTags);
    updateHiddenLanguagesField(selectedTags);  
}

function updateLangString(tags) {
    const langString = tags.join(' '); 
    if (langContainer) {
        langContainer.setAttribute('lang', langString);  
    }
}

function updateHiddenLanguagesField(tags) {
    let hiddenInput = document.getElementById('hidden-languages');
    if (!hiddenInput) {
        hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'languages';  
        hiddenInput.id = 'hidden-languages';
        hiddenFieldsContainer.appendChild(hiddenInput);
    }

    //Join the selected languages into a string and set it as the value
    hiddenInput.value = tags.join(' ');  //This will format them as e.g "nob nno sme"
}

function removeTag(tag) {
    const checkbox = Array.from(checkboxes).find(checkbox => checkbox.value === tag);
    if (checkbox) {
        checkbox.checked = false; 
    }
    updateTags();
}

dropdownToggle.addEventListener('click', function (event) {
    event.stopPropagation(); 
    dropdownMenu.classList.toggle('open');
});

document.addEventListener('click', function (event) {
    if (!dropdownMenu.contains(event.target) && !dropdownToggle.contains(event.target)) {
        dropdownMenu.classList.remove('open'); 
    }
});

checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', updateTags);
});

updateTags();
