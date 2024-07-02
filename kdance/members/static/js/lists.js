$(document).ready(() => {
  getSeasons();
  populateMainSelect();
  searchData();
  const mainSelect = document.querySelector('#menu-1-select');
  mainSelect.addEventListener('change', () =>
    onMainChange(mainSelect.value)
  );
});


function getSeasons() {
  $.ajax({
    url: seasonsUrl,
    type: 'GET',
    success: (data) => {
      data.map((season) => {
        let label = season.year;
        if (season.is_current) {
          label += ' (en cours)';
        }
        $('#season-select').append($('<option>', { value: season.id, text: label, selected: season.is_current }));
      });
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function populateMainSelect() {
  for (let [key, value] of Object.entries(LIST_MAIN_MAPPING)) {
    $('#menu-1-select').append($('<option>', { value: key, text: value, selected: key == '0' }));
  }
}

function populateSecondSelect(previousValue) {
  $('#menu-2-select').attr('hidden', false);
  switch (previousValue) {
    case '1':
      getCourses($('#season-select').val());
      break
    case '2':
      $('#menu-2-select').empty();
      for (let [key, value] of Object.entries(MONTH)) {
        $('#menu-2-select').append($('<option>', { value: key, text: value, selected: key == '0' }));
      }
      break
    default:
      $('#menu-2-select').empty();
      $('#menu-2-select').attr('hidden', true);
  }
}

function onMainChange(mainValue) {
  $('#menu-2-select').empty();
  if (mainValue == '0') {
    $('#menu-2-select').attr('hidden', true);
  } else {
    populateSecondSelect(mainValue);
  }
}


function getCourses(seasonId) {
  $.ajax({
    url: coursesUrl + `?season=${seasonId}`,
    type: 'GET',
    success: (data) => {
      $('#menu-2-select').append($('<option>', { value: '0', text: 'Tous les cours', selected: true }));
      for (let i = 0; i < data.length; i++) {
        $('#menu-2-select').append($('<option>', { value: data[i].id, text: data[i].name }));
      }
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function searchData() {
  $('#search-btn').on('click', () => {
    switch ($('#menu-1-select').val()) {
      case '1':
        getMembersPerCourse();
        break
      case '2':
        getChecksPerMonth();
        break
      default:
        return
    }
  });
}

function getMembersPerCourse() {
  document.querySelector('#total-amount-div').className = 'd-none';
  var url;
  if ($('#menu-2-select').val() === '0') {
    url = membersUrl + `?season=${$('#season-select').val()}`
  } else {
    url = membersUrl + `?course=${$('#menu-2-select').val()}`
  }
  $.ajax({
    url: url,
    type: 'GET',
    success: (data) => {
      $('#data-table').bootstrapTable('destroy');
      $('#data-table').bootstrapTable({
        search: true,
        stickyHeader: true,
        showFullscreen: true,
        showColumns: true,
        showExport: true,
        exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
        exportOptions: {
          fileName: function () {
            const suffix = $('#menu-2-select').val() === '0' ? 'tous' : $('#menu-2-select option:selected').text();
            return `adherents_${$('#season-select option:selected').text()}_${suffix}`
          }
        },
        // TODO: add responsibles and emergency contacts once available
        columns: [
          {
            field: 'last_name',
            title: 'Nom de famille',
            searchable: true,
            sortable: true,
          }, {
            field: 'first_name',
            title: 'Prénom',
            searchable: true,
            sortable: true,
          }, {
            field: 'phone',
            title: 'Téléphone',
            searchable: false,
            sortable: false,
          }, {
            field: 'email',
            title: 'Email',
            searchable: false,
            sortable: false,
          }, {
            field: 'courses',
            title: 'Cours',
            searchable: true,
            sortable: true,
            visible: false,
          }, {
            field: 'documents.authorise_photos',
            title: 'Autorisation photos',
            searchable: true,
            sortable: true,
            visible: false,
          }, {
            field: 'documents.authorise_emergency',
            title: 'Autorisation parentale',
            searchable: true,
            sortable: true,
            visible: false,
          }],
        data: data.map((m) => {
          return {
            ...m,
            courses: m.courses.map((c) => c.name),
            documents: {
              ...m.documents,
              authorise_photos: m.documents.authorise_photos ? 'Oui': 'Non',
              authorise_emergency: m.documents.authorise_emergency ? 'Oui': 'Non',
            }
          }
        })
      });
      $('input[type=search]').attr('placeholder', 'Rechercher');
      $('#total-count').text(data.length);
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function getChecksPerMonth() {
  if ($('#menu-2-select').val() === '0') {
    // Error message to be displayed, no month selected
    console.log('No month selected');
    return
  }
  $.ajax({
    url: checksUrl + `?season=${$('#season-select').val()}` + `&month=${$('#menu-2-select').val()}`,
    type: 'GET',
    success: (data) => {
      $('#data-table').bootstrapTable('destroy');
      $('#data-table').bootstrapTable({
        search: true,
        stickyHeader: true,
        showFullscreen: true,
        showColumns: true,
        showExport: true,
        exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
        exportOptions: {
          fileName: function () {
            const suffix = $('#menu-2-select').val() === '0' ? 'tous' : $('#menu-2-select option:selected').text();
            return `checks_${$('#season-select option:selected').text()}_${suffix}`
          }
        },
        columns: [
          {
            field: 'bank',
            title: 'Banque',
            searchable: true,
            sortable: true,
          }, {
            field: 'name',
            title: 'Emetteur',
            searchable: true,
            sortable: true,
          }, {
            field: 'number',
            title: 'Numéro de chèque',
            searchable: true,
            sortable: true,
          }, {
            field: 'amount',
            title: 'Montant (€)',
            searchable: true,
            sortable: true,
          }],
        data: data
      });
      $('input[type=search]').attr('placeholder', 'Rechercher');
      $('#total-count').text(data.length);
      document.querySelector('#total-amount-div').className = 'd-flex';
      const totalAmount = data.reduce(
        (acc, val) => acc + val.amount,
        0,
      );
      $('#total-amount').text(`${totalAmount}€`);
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}
