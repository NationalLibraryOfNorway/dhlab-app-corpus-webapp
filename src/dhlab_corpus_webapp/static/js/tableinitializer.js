let data_table = null;
let originalColumnDefs = null;
let tableMode = "simple";


function setColumnVisibility() {
    if (originalColumnDefs == null || originalColumnDefs == undefined)
        return;

    for (let i = 0; i < originalColumnDefs.length; i++){
        data_table.column(i).visible(tableMode == "detailed" || originalColumnDefs[i].visible);
    }
}



function initializeDataTable(table_selector, columnDefs) {
    originalColumnDefs = columnDefs;

    data_table = new DataTable(table_selector, {
        searching: true,
        info: true,
        responsive: true,
        paging: true,
        pageLength: 10,
        lengthChange: true,
        columnDefs: columnDefs,
        scrollX: (tableMode == "detailed"),
        order: [],
        layout: {
            bottomStart: {
                pageLength: {
                    menu: [ 10, 25, 50, 100 ],
                    text: '_MENU_ rader per side'
                }
            },
            bottomEnd: {
                search: {
                    placeholder: 'Skriv søkestreng her',
                    text: 'Søk i tabellen:'
                }
            },
            topStart: {
                info: {
                    text: 'Viser rad _START_ til _END_ av totalt _TOTAL_ rader'
                }
            },
            topEnd: {
                paging: {}
            }
        }
    });
    setColumnVisibility()

    return data_table;
}

/*
    We cannot dynamically update the horisontal scroll option, so we explicitly delete and recreate the datatable to update the scrolling.
*/
function recreateTable() {
    const tableSelector = data_table.table().node();
    data_table.destroy();
    initializeDataTable(tableSelector, originalColumnDefs)
}

function updateTableMode(newTableMode) {
    tableMode = newTableMode;
    if (data_table != null)
        recreateTable();
}
