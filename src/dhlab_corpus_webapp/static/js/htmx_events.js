/*
    The button for exploring a corpus is not in the same form as the corpus definition.
    This file adds an event listener that catches all HTMX-requests before sending them,
    checks if it was created by the "update-corpus-form"-form and if so, it includes the
    data from the "search-form-corpus" form.
*/
document.addEventListener(
    "htmx:configRequest",
    (htmxEvent) => {
        if (htmxEvent.target.id != "update-corpus-form"){
            return
        }

        let corpusBuilderForm = new FormData(document.getElementById("search-form-corpus"));
        corpusBuilderForm.forEach(
            (val, key) => {
                if (val instanceof File)
                    htmxEvent.detail.parameters[key] = [val];
                else if (key == "language")
                    htmxEvent.detail.parameters[key] = corpusBuilderForm.getAll(key).join(" OR ");
                else
                    htmxEvent.detail.parameters[key] = val;
            }
        )
    }
)


/*
    We want to clear the output whenever the exploration method changes
*/
document.addEventListener(
    "htmx:configRequest",
    (htmxEvent) => {
        if (htmxEvent.target.id == "exploration-method-form")
            document.getElementById("output").innerHTML = "";
    }
)


/*
    We want to scroll to the output element after replacing it
*/
document.addEventListener(
    "htmx:afterSettle",
    (htmxEvent) => {
        if (htmxEvent.target.id == "output")
            document.getElementById("output").scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
)
