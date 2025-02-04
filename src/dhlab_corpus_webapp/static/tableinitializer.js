function initializeDataTable(filename) { 
    new DataTable('#results_table', {
        dom: 'Bfrtip',
        responsive: true,
        buttons: [
            {
                extend: 'excel',
                filename: 'korpus'
            },
            {
                extend: 'csv',
                title: 'korpus', 
                bom: true, 
            }
        ]
    });
}



