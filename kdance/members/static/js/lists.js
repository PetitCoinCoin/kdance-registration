/************************************************************************************/
/* Copyright 2024 - present, Andréa Marnier                                              */
/*                                                                                  */
/* This file is part of KDance registration.                                        */
/*                                                                                  */
/* KDance registration is free software: you can redistribute it and/or modify it   */
/* under the terms of the GNU Affero General Public License as published by the     */
/* Free Software Foundation, either version 3 of the License, or any later version. */
/*                                                                                  */
/* KDance registration is distributed in the hope that it will be useful, but       */
/* WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or    */
/* FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License      */
/* for more details.                                                                */
/*                                                                                  */
/* You should have received a copy of the GNU Affero General Public License along   */
/* with KDance registration. If not, see <https://www.gnu.org/licenses/>.           */
/************************************************************************************/

$(document).ready(() => {
  getSeasons();
  searchData();
  populateMainSelect();
  const mainSelect = document.querySelector('#menu-1-select');
  mainSelect.addEventListener('change', () =>
    onMainChange(mainSelect.value)
  );
  document.querySelector('#season-select').addEventListener('change', () => {
    mainSelect.dispatchEvent(new Event('change'));
    $('#data-table').bootstrapTable('destroy');
    document.querySelector('#total-amount-div').className = 'd-none';
    $('#total-count').text(0);
  });
  breadcrumbDropdownOnHover();
});


function getSeasons() {
  getSeasonsWrapper((data) => {
    data.map((season) => {
      let label = season.year;
      if (season.is_current) {
        label += ' (en cours)';
      }
      $('#season-select').append($('<option>', { value: season.id, text: label, selected: season.is_current }));
    });
  }, LISTS_TOAST_PREFIX);
}

function populateMainSelect() {
  for (let [key, value] of Object.entries(LIST_MAIN_MAPPING)) {
    $('#menu-1-select').append($('<option>', { value: key, text: value, selected: key == '0' }));
  }
}

function populateSecondSelect(previousValue) {
  $('#menu-2-select').attr('hidden', false);
  $('#menu-2-select').empty();
  switch (previousValue) {
    case '1':
    case '6':
    case '7':
    case '8':
      getCourses($('#season-select').val(), previousValue);
      break
    case '9':
      getCourses($('#season-select').val(), previousValue, true);
      break
    case '3':
      for (let [key, value] of Object.entries(MONTH)) {
        $('#menu-2-select').append($('<option>', { value: key, text: value, selected: key == '0' }));
      }
      break
    default:
      $('#menu-2-select').attr('hidden', true);
  }
}

function onMainChange(mainValue) {
  $('#menu-2-select').empty();
  const empty_one = ['0', '2', '4', '5'];
  if (empty_one.indexOf(mainValue) > -1) {
    $('#menu-2-select').attr('hidden', true);
  } else {
    populateSecondSelect(mainValue);
  }
}

function getCourses(seasonId, mainValue, isForNextSeason = false) {
  const filter = isForNextSeason ? '&next=true' : ''
  $.ajax({
    url: coursesUrl + `?season=${seasonId}`+ filter,
    type: 'GET',
    success: (data) => {
      $('#menu-2-select').append($('<option>', { value: '0', text: ['6', '8', '9'].indexOf(mainValue) > -1 ? '-' : 'Tous les cours', selected: true }));
      for (let i = 0; i < data.length; i++) {
        const startHour = data[i].start_hour.split(':');
        const label = `${data[i].name}, ${WEEKDAY[data[i].weekday]} ${startHour[0]}h${startHour[1]}`;
        $('#menu-2-select').append($('<option>', { value: data[i].id, text: label }));
      }
    },
    error: (error) => {
      showToast('Impossible de récupérer les cours de la saison.', LISTS_TOAST_PREFIX);
      console.log(error);
    }
  });
}

function searchData() {
  $('#search-btn').on('click', () => {
    showLoader();
    const mainValue = $('#menu-1-select').val();
    switch (mainValue) {
      case '1':
      case '4':
      case '5':
      case '6':
      case '7':
      case '8':
      case '9':
        getMembersPerCourse(mainValue);
        break
      case '2':
        getPayments();
        break;
      case '3':
        getChecksPerMonth();
        break
      default:
        break
    }
  });
}

function getMembersPerCourse(mainValue) {
  document.querySelector('#total-amount-div').className = 'd-none';
  var url;
  const subValue = $('#menu-2-select').val()
  let filter = '';
  switch (subValue) {
    case null:
      switch (mainValue) {
        case '4':
          filter = 'with_pass';
          break
        case '5':
          filter = 'with_license';
          break
        default:
          console.log('This should not happen');
          return
      }
      url = `${membersUrl}?season=${$('#season-select').val()}&${filter}=true`;
      break
    case '0':
      if (mainValue === '6' || mainValue === '8' || mainValue === '9') {
        const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('list-error-toast'));
        $('#list-error-body').text('Veuillez sélectionner un cours.');
        toast.show();
        return
      }
      url = `${membersUrl}?season=${$('#season-select').val()}`;
      break
    default:
      if (mainValue == '9') {
        filter = '&next=true'
      }
      url = `${membersUrl}?course=${subValue}${filter}`;
  }
  $.ajax({
    url: url,
    type: 'GET',
    success: (data) => {
      $('#data-table').bootstrapTable('destroy');
      switch (mainValue) {
        case '1':
        case '9':
          buildMembersInfo(data, subValue, mainValue === '9');
          break
        case '2':
        case '3':
          console.log('This should not happen');
          return
        case '4':
          buildSportPassInfo(data);
          break
        case '5':
          buildLicenseInfo(data);
          break
        case '6':
          buildContactInfo(data);
          break
        case '7':
          buildEmergencyInfo(data, subValue);
          break
        case '8':
          buildNextSeason(data, subValue);
          break;
        default:
          return
      }
      $('#total-count').text(data.length);
    },
    error: (error) => {
      showToast('Impossible de récupérer les informations.', LISTS_TOAST_PREFIX);
      console.log(error);
    },
    complete: () => {
      hideLoader();
    }
  });
}

function buildMembersInfo(data, courseId, isForNextSeason) {
  let columns = [
    {
      field: 'name',
      title: 'Adhérent',
      searchable: true,
      sortable: true,
    },
    {
      field: 'birthday',
      title: 'Date de naissance',
      searchable: false,
      sortable: true,
    }
  ];
  if (isForNextSeason) {
    columns.push({
        field: 'current_courses',
        title: 'Cours actuels',
        searchable: false,
        sortable: true,
        visible: true,
        formatter: function(value) {
          return value.join('<br />')
        },
      })
  } else {
    columns.push(...[
    {
      field: 'created',
      title: 'Inscrit le',
      searchable: false,
      sortable: true,
      visible: false,
    }, {
      field: 'status',
      title: 'Statut',
      searchable: true,
      sortable: true,
      visible: true,
      formatter: function(value) {
        return value.join('<br />')
      },
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
      field: 'address',
      title: 'Adresse',
      searchable: false,
      sortable: false,
      visible: false,
    }, {
      field: 'postal_code',
      title: 'Code',
      searchable: false,
      sortable: false,
      visible: false,
    }, {
      field: 'city',
      title: 'Ville',
      searchable: true,
      sortable: true,
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
      visible: false,
    }, {
      field: 'phone-emergency-1',
      title: 'Tél urgence 1',
      searchable: false,
      sortable: false,
      visible: false,
    }, {
      field: 'name-emergency-2',
      title: 'Contact urgence 2',
      searchable: true,
      sortable: true,
      visible: false,
    }, {
      field: 'phone-emergency-2',
      title: 'Tél urgence 2',
      searchable: false,
      sortable: false,
      visible: false,
    }, {
      field: 'documents.authorise_photos',
      title: 'Autorisation photos',
      searchable: false,
      sortable: true,
      visible: false,
    }, {
      field: 'documents.authorise_emergency',
      title: 'Autorisation parentale',
      searchable: false,
      sortable: true,
      visible: false,
    }
  ]);
    if (courseId > 0) {
      columns.splice(5, 0, {
        field: 'courses',
        title: 'Autre cours',
        searchable: true,
        sortable: true,
        visible: true,
        formatter: function(value) {
          return value.join('<br />')
        },
      }
    );
    }
  }
  $('#data-table').bootstrapTable({
    ...COMMON_TABLE_PARAMS,
    showExport: true,
    exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
    exportOptions: {
      fileName: function () {
        const suffix = $('#menu-2-select').val() === '0' ? 'tous' : $('#menu-2-select option:selected').text();
        return `adherents_${$('#season-select option:selected').text().substring(0,9)}_${suffix}`
      }
    },
    columns: columns,
    data: data.map(m => {
      if (isForNextSeason) {
        return {
          birthday: (new Date(m.birthday)).toLocaleDateString('fr-FR'),
          name: `${m.last_name} ${m.first_name}`,
          current_courses: m.active_courses.map(
          (c) => `${c.name}, ${WEEKDAY[c.weekday]}`
        ).concat(m.cancelled_courses.map(
          (c) => `${c.name}, ${WEEKDAY[c.weekday]} (Annulé)`)
        ),
        }
      }
      return {
        ...m,
        status: courseId > 0 ? buildStatusOneCourse(m, courseId) : buildStatusAllCourses(m),
        birthday: (new Date(m.birthday)).toLocaleDateString('fr-FR'),
        created: (new Date(m.created)).toLocaleString('fr-FR'),
        name: `${m.last_name} ${m.first_name}`,
        courses: m.active_courses.filter(c => c.id != courseId).map(
          (c) => `${c.name}, ${WEEKDAY[c.weekday]}`
        ).concat(m.waiting_courses.filter(c => c.id != courseId).map(
          (c) => `${c.name}, ${WEEKDAY[c.weekday]} (Liste d'attente)`)
        ).concat(m.cancelled_courses.filter(c => c.id != courseId).map(
          (c) => `${c.name}, ${WEEKDAY[c.weekday]} (Annulé)`)
        ),
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

function buildStatusAllCourses(member) {
  const active = member.active_courses.length > 0 ?
    (member.is_validated ? '<u>Payé</u><br />' : '<u>Non payé</u><br />') + member.active_courses.map(
      (c) => `- ${c.name}, ${WEEKDAY[c.weekday]}`
    ).join('<br />')
    : undefined;
  const waiting = member.waiting_courses.length > 0 ?
    '<u>Sur liste d\'attente</u><br />' + member.waiting_courses.map(
      (c) => `- ${c.name}, ${WEEKDAY[c.weekday]}`
    ).join('<br />')
    : undefined;
  const cancelled = member.cancelled_courses.length > 0 ?
    '<u>Annulé</u><br />' + member.cancelled_courses.map(
      (c) => `- ${c.name}, ${WEEKDAY[c.weekday]}`
    ).join('<br />')
    : undefined;
  return [active, waiting, cancelled]
}

function buildStatusOneCourse(member, courseId) {
  if (member.waiting_courses.map(c => c.id.toString()).indexOf(courseId) >= 0) {
    return ['Sur liste d\'attente']
  }
  if (member.cancelled_courses.map(c => c.id.toString()).indexOf(courseId) >= 0) {
    return ['Annulé']
  }
  return [member.is_validated ? 'Payé' : 'Non payé']
}

function buildEmergencyInfo(data, courseId) {
  $('#data-table').bootstrapTable({
    ...COMMON_TABLE_PARAMS,
    showExport: true,
    exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
    exportOptions: {
      fileName: function () {
        const suffix = $('#menu-2-select').val() === '0' ? 'tous' : $('#menu-2-select option:selected').text();
        return `urgences_${$('#season-select option:selected').text().substring(0,9)}_${suffix}`
      }
    },
    columns: [
      {
        field: 'name',
        title: 'Adhérent',
      }, {
        field: 'name-responsible-1',
        title: 'Responsable légal 1',
      }, {
        field: 'phone-responsible-1',
        title: 'Tél 1',
      }, {
        field: 'name-responsible-2',
        title: 'Responsable légal 2',
      }, {
        field: 'phone-responsible-2',
        title: 'Tél 2',
      }, {
        field: 'name-emergency-1',
        title: 'Contact urgence 1',
      }, {
        field: 'phone-emergency-1',
        title: 'Tél urgence 1',
      }, {
        field: 'name-emergency-2',
        title: 'Contact urgence 2',
      }, {
        field: 'phone-emergency-2',
        title: 'Tél urgence 2',
      }, {
        field: 'authorise_emergency',
        title: 'Autorisation parentale',
      }, {
        field: 'courses',
        title: 'Cours',
        visible: false,
        searchable: true,
        sortable: true,
        formatter: function(value) {
          return value.join('<br />')
        },
      }],
    data: data.filter(m =>
      courseId > 0
      ? m.active_courses.map(c => c.id.toString()).indexOf(courseId) >= 0
      : m.active_courses.length > 0
    ).map(m => {
      return {
        ...m,
				name: `${m.last_name} ${m.first_name}`,
        birthday:(new Date(m.birthday)).toLocaleDateString('fr-FR'),
        authorise_emergency: m.documents.authorise_emergency ? 'Oui': 'Non',
        courses: m.active_courses.map((c) => `- ${c.name}, ${WEEKDAY[c.weekday]}`),
        ...buildContactsData(m.contacts),
      }
    })
  });
}

function buildNextSeason(data, courseId) {
  const seasonId = $('#season-select').val();
  if (! nextSeasonId) {
    showToast('Il n\'y a pas encore de saison prochaine. Allez d\'abord la créer et ajouter des cours !', LISTS_TOAST_PREFIX, false);
    return;
  }
  showLoader();
  $.ajax({
    url: coursesUrl + `?season=${seasonId}&next=true`,
    type: 'GET',
    success: (coursesData) => {
      hideLoader();
      let columns = [
        {
          field: 'name',
          title: 'Adhérent',
          searchable: true,
          sortable: true,
        },{
          field: 'birthyear',
          title: 'Né(e) en',
          searchable: false,
          sortable: true,
          width: '100',
        }, {
          field: 'courses',
          title: 'Autre cours',
          searchable: true,
          sortable: true,
          visible: true,
          formatter: function(value) {
            return value.join('<br />')
          },
        }, {
          field: 'operate',
          title: 'Cours pour l\'année prochaine',
          align: 'left',
          clickToSelect: false,
          formatter: actionFormatter,
        }
      ];
      $('#data-table').bootstrapTable({
        ...COMMON_TABLE_PARAMS,
        showExport: true,
        exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
        exportOptions: {
          fileName: function () {
            const suffix = $('#menu-2-select').val() === '0' ? 'tous' : $('#menu-2-select option:selected').text();
            return `adherents_prochaine-saison_${$('#season-select option:selected').text().substring(0,9)}_${suffix}`
          }
        },
        columns: columns,
        data: data.map(m => {
          const birthyear = (new Date(m.birthday)).getFullYear();
          return {
            ...m,
            name: `${m.last_name} ${m.first_name}`,
            birthyear,
            courses: m.active_courses.filter(c => c.id != courseId).map(
              (c) => `${c.name}, ${WEEKDAY[c.weekday]}`
            ),
            possibleCourses: coursesData.filter((c) => (! c.min_year || c.min_year <= birthyear) && c.max_year >= birthyear)
          }
        })
      });
    },
    error: (error) => {
      showToast('Êtes vous sur d\'avoir créé la saison prochaine ? Allez d\'abord la créer et ajouter des cours ! À moins qu\'il y ait un autre problème.', LISTS_TOAST_PREFIX, false);
      console.log(error);
    }
  });
}

function actionFormatter(value, row, index) {
  const possibleCourses = row.possibleCourses.map((c) =>
    `<li class="form-check">
        <input type="checkbox" class="form-check-input" id="${row.id}-${c.id}"${row.next_courses.map(i => i.id).indexOf(c.id) > -1 ? ' checked' : ''} onChange=updateNextSeason(event,${row.id},${c.id})>
        <label class="form-check-label" for="${row.id}-${c.id}">${c.name} (${c.min_year ? `${c.min_year}-${c.max_year}` : `≤${c.max_year}`}), ${WEEKDAY[c.weekday]}</label>
      </li>`
  );
  return `<div id="next-${row.id}" class="d-flex flex-column">
  ${row.next_courses.map((c) => `<span id="next-${row.id}-${c.id}">${c.name}, ${WEEKDAY[c.weekday]}</span>`).join('')}
  </div>
  <div class="dropdown mt-2">
  <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false" data-bs-auto-close="outside">
    Ajuster l'affectation
  </button>
  <ul class="dropdown-menu p-2">${possibleCourses.join('')}</ul></div>`
}

function updateNextSeason(event, memberId, courseId) {
  const action = event.target.checked ? 'add' : 'remove';
  $.ajax({
    url: membersUrl + memberId + '/next-courses/' + action + '/',
    type: 'PUT',
    contentType: 'application/json',
    headers: { 'X-CSRFToken': csrftoken },
    mode: 'same-origin',
    data: JSON.stringify({ next_course: courseId }),
    dataType: 'json',
    success: (data) => {
      if (action === 'add') {
        $(`#next-${memberId}`)[0].innerHTML += `<span id="next-${memberId}-${courseId}">${data.name}, ${WEEKDAY[data.weekday]}</span>`
      } else {
        $(`#next-${memberId}-${courseId}`)[0].remove()
      }
      showToast('Affectation mise à jour !', 'list-success', false);
    },
    error: (error) => {
      if (!error.responseJSON) {
        showToast(DEFAULT_ERROR, LISTS_TOAST_PREFIX);
        console.log(error);
      }
    }
  });
}

function buildContactsData(data) {
  let contacts = {};
  Object.keys(CONTACT_MAPPING).forEach(key => {
    const subContacts = data.filter(c => c.contact_type === key);
    // Technically, we could have 3 contacts per type. But this is higly unusual
    for (i=0; i<CONTACT_NUMBER; i++) {
      contacts[`name-${key}-${i+1}`] = i < subContacts.length ? `${subContacts[i].first_name} ${subContacts[i].last_name}` : undefined;
      contacts[`phone-${key}-${i+1}`] = i < subContacts.length ? subContacts[i].phone : undefined;
      if (key === 'responsible') {
        contacts[`email-${key}-${i+1}`] = i < subContacts.length ? subContacts[i].email : undefined;
      }
    }
  });
  return contacts
}

function buildContactInfo(data) {
  $('#data-table').bootstrapTable({
    ...COMMON_TABLE_PARAMS,
    showExport: true,
    exportTypes: ['csv'],
    exportOptions: {
      fileName: function () {
        const suffix = $('#menu-2-select').val() === '0' ? 'tous' : $('#menu-2-select option:selected').text();
        return `contacts_${$('#season-select option:selected').text().substring(0,9)}_${suffix}`
      }
    },
    columns: [
      {
        field: 'last_name',
        title: 'Last Name',
      }, {
        field: 'first_name',
        title: 'First Name',
      }, {
        field: 'suffix',
        title: 'Name Suffix',
      }, {
        field: 'phone',
        title: 'Phone',
      }, {
        field: 'email',
        title: 'Email',
      }, {
        field: 'courses',
        title: 'Cours',
        formatter: function(value) {
          return value.join('<br />')
        },
      }],
    data: data.map(m => {
      return {
        ...m,
        suffix: '',
        courses: m.active_courses.map((c) => `- ${c.name}, ${WEEKDAY[c.weekday]}`).concat(m.cancelled_courses.map((c) => `- ${c.name}, ${WEEKDAY[c.weekday]} (Annulé)`)).concat(m.waiting_courses.map((c) => `- ${c.name}, ${WEEKDAY[c.weekday]} (En attente)`)),
      }
    }).concat(data.map(m => buildResponsibleContactData(m.contacts, m.first_name, m.last_name)).flat())
  });
}

function buildResponsibleContactData(data, memberFirstname, memberLastname) {
  return data.filter(c => c.contact_type === 'responsible').map(c => {
    return {
      first_name: c.first_name,
      last_name: c.last_name,
      suffix: `(${memberFirstname} ${memberLastname})`,
      email: c.email,
      phone: c.phone,
      courses: [],
    }
  });
}

function buildSportPassInfo(data) {
  $('#data-table').bootstrapTable({
    ...COMMON_TABLE_PARAMS,
    showExport: true,
    exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
    exportOptions: {
      fileName: function () {
        return `pass-sport_${$('#season-select option:selected').text().substring(0,9)}`
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
        field: 'email',
        title: 'Email',
        searchable: false,
        sortable: false,
      }, {
        field: 'sport_pass.amount',
        title: 'Montant (€)',
        searchable: false,
        sortable: false,
      }, {
        field: 'birthday',
        title: 'Date de naissance',
      }, {
        field: 'address',
        title: 'Adresse',
        visible: false,
      }, {
        field: 'name-responsible-1',
        title: 'Responsable légal',
      }, {
        field: 'phone-responsible-1',
        title: 'Téléphone responsable',
      }, {
        field: 'email-responsible-1',
        title: 'Email responsable',
      },
    ],
    data: data.filter(m => m.sport_pass !== null).map((m) => {
      return {
        ...m,
        member: `${m.first_name} ${m.last_name}`,
        email: m.email,
        birthday:(new Date(m.birthday)).toLocaleDateString('fr-FR'),
        address: `${m.address}, ${m.postal_code} ${m.city}`,
        ...buildContactsData(m.contacts),
      }
    })
  });
}

function buildLicenseInfo(data) {
  $('#data-table').bootstrapTable({
    ...COMMON_TABLE_PARAMS,
    showExport: true,
    exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
    exportOptions: {
      fileName: function () {
        return `licences_${$('#season-select option:selected').text().substring(0,9)}`
      }
    },
    columns: [
      {
        field: 'member',
        title: 'Adhérent',
        searchable: true,
        sortable: true,
      }, {
        field: 'email',
        title: 'Email',
      }, {
        field: 'license',
        title: 'Licence FFD',
        searchable: true,
        sortable: true,
      }, {
        field: 'birthday',
        title: 'Date de naissance',
      }, {
        field: 'address',
        title: 'Adresse',
      }, {
        field: 'name-responsible-1',
        title: 'Responsable légal',
      }, {
        field: 'phone-responsible-1',
        title: 'Téléphone responsable',
      }, {
        field: 'email-responsible-1',
        title: 'Email responsable',
      },
    ],
    data: data.map((m) => {
      return {
        member: `${m.first_name} ${m.last_name}`,
        email: m.email,
        birthday: (new Date(m.birthday)).toLocaleDateString('fr-FR'),
        address: `${m.address}, ${m.postal_code} ${m.city}`,
        license: getLicenseLabel(m.ffd_license),
        ...buildContactsData(m.contacts),
      }
    })
  });
}

function getLicenseLabel(value) {
  switch (value.toString()) {
    case "0":
      return 'Aucune'
    case ffdA:
      return 'Licence A Loisir'
    case ffdB:
      return 'Licence B Compétiteur'
    case ffdC:
      return 'Licence C Compétiteur national'
    case ffdD:
      return 'Licence D Compétiteur international'
    default:
      return 'Inconnu'
  }
}

function getChecksPerMonth() {
  if ($('#menu-2-select').val() === '0') {
    const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('list-error-toast'));
    $('#list-error-body').text('Veuillez sélectionner un mois.');
    toast.show();
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
            return `checks_${$('#season-select option:selected').text().substring(0,9)}_${suffix}`
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
      $('#total-count').text(data.length);
      document.querySelector('#total-amount-div').className = 'd-flex';
      const totalAmount = data.reduce(
        (acc, val) => acc + val.amount,
        0,
      );
      $('#total-amount').text(`${totalAmount}€`);
    },
    error: (error) => {
      showToast('Impossible de récupérer les chèques demandés.', LISTS_TOAST_PREFIX);
      console.log(error);
    },
    complete: () => {
      hideLoader();
    }
  });
}

function idFormatter() {
  return 'Total'
}

function totalCountFormatter(data) {
  var field = this.field
  const access = (path, object) => {
    return path.split('.').reduce((o, i) => o[i], object)
  }
  return data.map(row => access(field, row)).reduce((acc, val) => {
    return acc + val || 0
  }, 0)
}

function totalAmountFormatter(data) {
  var field = this.field
  const access = (path, object) => {
    return path.split('.').reduce((o, i) => o[i], object)
  }
  return data.map(row => access(field, row)).reduce((acc, val) => {
    return acc + val || 0
  }, 0) + '€'
}

function getPayments() {
  $.ajax({
    url: `${paymentsUrl}?season=${$('#season-select').val()}`,
    type: 'GET',
    success: (data) => {
      hideLoader();
      $('#data-table').bootstrapTable('destroy');
      $('#data-table').bootstrapTable({
        ...COMMON_TABLE_PARAMS,
        showExport: true,
        showFooter: true,
        exportTypes: ['csv', 'xlsx', 'pdf', 'json'],
        exportOptions: {
          fileName: function () {
            return `paiements_${$('#season-select option:selected').substring(0,9).text()}`
          }
        },
        columns: [
          {
            field: 'user_email',
            title: 'Compte',
            searchable: true,
            sortable: true,
            footerFormatter: idFormatter,
          }, {
            field: 'due',
            title: 'Total dû',
            sortable: true,
            footerFormatter: totalAmountFormatter,
          }, {
            field: 'paid',
            title: 'Total payé',
            sortable: true,
            footerFormatter: totalAmountFormatter,
          }, {
            field: 'cash',
            title: 'Espèces',
            sortable: true,
            footerFormatter: totalAmountFormatter,
          }, {
            field: 'cb_payment',
            title: 'En ligne',
            sortable: true,
            footerFormatter: totalAmountFormatter,
          }, {
            field: 'check_count',
            title: 'Nb chèques',
            sortable: true,
            visible: false,
            footerFormatter: totalCountFormatter,
          }, {
            field: 'check_amount',
            title: 'Chèques (€)',
            sortable: true,
            footerFormatter: totalAmountFormatter,
          }, {
            field: 'sport_pass_count',
            title: 'Nb Pass Sport',
            sortable: true,
            visible: false,
            footerFormatter: totalCountFormatter,
          }, {
            field: 'sport_pass_amount',
            title: 'Pass Sport (€)',
            sortable: true,
            footerFormatter: totalAmountFormatter,
          }, {
            field: 'ancv.count',
            title: 'Nb ANCV',
            sortable: true,
            visible: false,
            footerFormatter: totalCountFormatter,
          }, {
            field: 'ancv.amount',
            title: 'ANCV (€)',
            sortable: true,
            footerFormatter: totalAmountFormatter,
          }, {
            field: 'sport_coupon.count',
            title: 'Nb Coupons Sport',
            sortable: true,
            visible: false,
            footerFormatter: totalCountFormatter,
          }, {
            field: 'sport_coupon.amount',
            title: 'Coupons Sport (€)',
            sortable: true,
            footerFormatter: totalAmountFormatter,
          }, {
            field: 'other_payment.amount',
            title: 'Autre (€)',
            sortable: true,
            footerFormatter: totalAmountFormatter,
          }, {
            field: 'refund',
            title: 'Remboursement (€)',
            sortable: true,
            footerFormatter: totalAmountFormatter,
          }, {
            field: 'special_discount',
            title: 'Remise exceptionnelle (€)',
            sortable: true,
            footerFormatter: totalAmountFormatter,
          }, {
            field: 'comment',
            title: 'Commentaire',
            sortable: true,
            searchable: true,
          }],
        data: data.map(p => {
          const checks = p.check_payment.filter(c => c.month !== 100)
          return {
            ...p,
            ancv: p.ancv || {amount: 0, count: 0},
            cb_payment: p.cb_payment?.amount || 0,
            sport_coupon: p.sport_coupon || {amount: 0, count: 0},
            other_payment: p.other_payment || {amount: 0, comment: ''},
            check_count: checks.length,
            check_amount: checks.reduce((acc, val) => acc + val.amount, 0),
          }
        })
      });
      $('#total-count').text(data.length);
      document.querySelector('#total-amount-div').className = 'd-flex';
      const totalAmount = data.reduce(
        (acc, val) => acc + val.paid,
        0,
      );
      $('#total-amount').text(`${totalAmount}€`);
    },
    error: (error) => {
      hideLoader();
      showToast('Impossible de récupérer les paiements demandés.', LISTS_TOAST_PREFIX);
      console.log(error);
    }
  });
}
