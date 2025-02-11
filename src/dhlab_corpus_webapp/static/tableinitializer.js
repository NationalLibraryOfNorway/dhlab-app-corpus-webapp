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
                title: 'korpus', 
                bom: true, 
            }
        ]
    });
}



