function initializeDataTable(filename) {
    new DataTable('#results_table', {
        paging: true,
        responsive: true, //makes the table fit different screen sizes by auto adjusting
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


