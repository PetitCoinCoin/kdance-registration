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
      showToast('Impossible de récupérer la liste des saisons.');
      console.log(error);
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
  const empty_one = ['0', '3', '4'];
  if (empty_one.indexOf(mainValue) > -1) {
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
      showToast('Impossible de récupérer les cours de la saison.');
      console.log(error);
    }
  });
}

function searchData() {
  $('#search-btn').on('click', () => {
    const mainValue = $('#menu-1-select').val();
    switch (mainValue) {
      case '1':
      case '3':
      case '4':
        getMembersPerCourse(mainValue);
        break
      case '2':
        getChecksPerMonth();
        break
      default:
        return
    }
  });
}

function getMembersPerCourse(mainValue) {
  document.querySelector('#total-amount-div').className = 'd-none';
  var url;
  const subValue = $('#menu-2-select').val()
  switch (subValue) {
    case null:
      let filter = '';
      switch (mainValue) {
        case '3':
          filter = 'with_pass';
          break
        case '4':
          filter = 'with_license';
          break
        default:
          console.log('This should not happen');
          return
      }
      url = `${membersUrl}?season=${$('#season-select').val()}&${filter}=true`;
      break
    case '0':
      url = `${membersUrl}?season=${$('#season-select').val()}`;
      break
    default:
      url = `${membersUrl}?course=${subValue}`;
  }
  $.ajax({
    url: url,
    type: 'GET',
    success: (data) => {
      $('#data-table').bootstrapTable('destroy');
      switch (mainValue) {
        case '1':
          buildMembersInfo(data);
          break
        case '2':
          console.log('This should not happen');
          return
        case '3':
          buildSportPassInfo(data);
          break
        case '4':
          buildLicenseInfo(data);
          break
        default:
          return
      }
      $('input[type=search]').attr('placeholder', 'Rechercher');
      $('#total-count').text(data.length);
    },
    error: (error) => {
      showToast('Impossible de récupérer les informations.');
      console.log(error);
    }
  });
}

function buildMembersInfo(data) {
  $('#data-table').bootstrapTable({
    ...COMMON_TABLE_PARAMS,
    exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
    exportOptions: {
      fileName: function () {
        const suffix = $('#menu-2-select').val() === '0' ? 'tous' : $('#menu-2-select option:selected').text();
        return `adherents_${$('#season-select option:selected').text()}_${suffix}`
      }
    },
    columns: [
      {
        field: 'name',
        title: 'Adhérent',
        searchable: true,
        sortable: true,
      }, 
      {
        field: 'created',
        title: 'Inscrit le',
        searchable: false,
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
        field: 'name-responsible-1',
        title: 'Responsable légal 1',
        searchable: true,
        sortable: true,
        visible: false,
      }, {
        field: 'phone-responsible-1',
        title: 'Tél 1',
        searchable: false,
        sortable: false,
        visible: false,
      }, {
        field: 'email-responsible-1',
        title: 'Email 1',
        searchable: false,
        sortable: false,
        visible: false,
      }, {
        field: 'name-responsible-2',
        title: 'Responsable légal 2',
        searchable: true,
        sortable: true,
        visible: false,
      }, {
        field: 'phone-responsible-2',
        title: 'Tél 2',
        searchable: false,
        sortable: false,
        visible: false,
      }, {
        field: 'email-responsible-2',
        title: 'Email 2',
        searchable: false,
        sortable: false,
        visible: false,
      }, {
        field: 'name-emergency-1',
        title: 'Contact urgence 1',
        searchable: true,
        sortable: true,
      }, {
        field: 'phone-emergency-1',
        title: 'Tél urgence 1',
        searchable: false,
        sortable: false,
      }, {
        field: 'name-emergency-2',
        title: 'Contact urgence 2',
        searchable: true,
        sortable: true,
      }, {
        field: 'phone-emergency-2',
        title: 'Tél urgence 2',
        searchable: false,
        sortable: false,
      }, {
        field: 'courses',
        title: 'Cours',
        searchable: true,
        sortable: true,
        visible: false,
        formatter: function(value) {
          return value.join('<br>')
        },
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
    data: data.map(m => {
      return {
        ...m,
        created: (new Date(m.created)).toLocaleString('fr-FR'),
        name: `${m.last_name} ${m.first_name}`,
        courses: m.active_courses.map((c) => `- ${c.name}, ${WEEKDAY[c.weekday]}`).concat(m.cancelled_courses.map((c) => `- ${c.name}, ${WEEKDAY[c.weekday]} (Annulé)`)),
        documents: {
          ...m.documents,
          authorise_photos: m.documents.authorise_photos ? 'Oui': 'Non',
          authorise_emergency: m.documents.authorise_emergency ? 'Oui': 'Non',
        },
        ...buildContactsData(m.contacts),
      }
    })
  });
}

function buildContactsData(data) {
  let contacts = {};
  Object.keys(CONTACT_MAPPING).forEach(key => {
    const subContacts = data.filter(c => c.contact_type === key);
    // Technically, we could have 3 contacts per type. But this is higly unusual
    for (i=0; i<CONTACT_ALL_NUMBER; i++) {
      contacts[`name-${key}-${i+1}`] = i < subContacts.length ? `${subContacts[i].first_name} ${subContacts[i].last_name}` : undefined;
      contacts[`phone-${key}-${i+1}`] = i < subContacts.length ? subContacts[i].phone : undefined;
      if (key === 'responsible') {
        contacts[`email-${key}-${i+1}`] = i < subContacts.length ? subContacts[i].phone : undefined;
      }
    }
  });
  return contacts
}

function buildSportPassInfo(data) {
  $('#data-table').bootstrapTable({
    ...COMMON_TABLE_PARAMS,
    exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
    exportOptions: {
      fileName: function () {
        return `pass-sport_${$('#season-select option:selected').text()}`
      }
    },
    columns: [
      {
        field: 'sport_pass.code',
        title: 'Code Pass Sport',
        searchable: true,
        sortable: true,
      }, {
        field: 'member',
        title: 'Adhérent',
        searchable: true,
        sortable: true,
      }, {
        field: 'sport_pass.amount',
        title: 'Montant (€)',
        searchable: false,
        sortable: false,
      }],
    data: data.filter(m => m.sport_pass !== null).map((m) => {
      return {
        ...m,
        member: `${m.first_name} ${m.last_name}`
      }
    })
  });
}

function buildLicenseInfo(data) {
  $('#data-table').bootstrapTable({
    ...COMMON_TABLE_PARAMS,
    exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
    exportOptions: {
      fileName: function () {
        return `licences_${$('#season-select option:selected').text()}`
      }
    },
    columns: [
      {
        field: 'member',
        title: 'Adhérent',
        searchable: true,
        sortable: true,
      }, {
        field: 'license',
        title: 'Licence FFD',
        searchable: true,
        sortable: true,
      }],
    data: data.map((m) => {
      return {
        member: `${m.first_name} ${m.last_name}`,
        license: LICENSES[m.ffd_license],
      }
    })
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
        ...COMMON_TABLE_PARAMS,
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
      showToast('Impossible de récupérer les chèques demandés.');
      console.log(error);
    }
  });
}

function showToast(text) {
  const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('list-error-toast'));
  $('#list-error-body').text(`${text} ${ERROR_SUFFIX}`);
  toast.show();
}