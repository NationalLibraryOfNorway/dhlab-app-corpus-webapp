function initializeDataTable(filename) {
    new DataTable('#results_table', {
        "dom": 'Bfrtip',
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


