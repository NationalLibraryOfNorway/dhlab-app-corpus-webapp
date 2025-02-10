function initializeDataTable(filename) { 
    new DataTable('#results_table', {
        dom: 'Bfrtip',
        responsive: true,
        buttons: [
            {
                extend: 'excel',
                filename: 'korpus',
                title: null
            },
            {
                extend: 'csv',
                filename: 'korpus', 
            }
        ]
    });
}



