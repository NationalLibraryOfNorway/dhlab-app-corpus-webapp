new DataTable('#results_table', {
        dom: 'frtipB',
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
                bom: true, 

            }
        ]
    });



