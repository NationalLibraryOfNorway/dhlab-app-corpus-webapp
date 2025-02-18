function initializeDataTable(filename) { 
    new DataTable('#results_table', {
        dom: 'frtipB',
        responsive: true,
        buttons: [
            {
                extend: 'excel',
                filename: 'korpus'
            },
            {
                extend: 'csv',
                filename: 'korpus', 
                bom: true, 
            }
        ]
    });
}



