function initializeDataTable(filename) {
    new DataTable('#results_table', {
        layout: {
            topStart: 'buttons'
        },
        buttons: [
            {
                extend: 'csv',
                text: 'Last ned data i csv-format',
                filename: filename
            },
            {
                extend: 'excel',
                text: 'Last ned data i excel-format',
                filename: filename
            }
        ]
    });
}


