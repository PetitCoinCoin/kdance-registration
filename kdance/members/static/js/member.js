$(document).ready(() => {
  getMember();
  activatePopovers();
  createUpdateMember();
  initContacts();
  handleContacts();
  handleSwitches();
  const birthdaySelect = document.querySelector('#member-birthday');
  birthdaySelect.addEventListener('change', () => {
    const isMajor = Boolean(getAge($('#member-birthday').val()) >= 18);
    majorityImpact(isMajor);
  });
});

function activatePopovers() {
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
}

function handleSwitches() {
  const meSwitch = document.querySelector('#me-switch');
  meSwitch.addEventListener('change', () => {
    const isMe = $('#me-switch').is(':checked');
    $('#member-email').val(isMe ? document.querySelector('#form-member').getAttribute('data-bs-email') : '');
    $('#member-phone').val(isMe ? document.querySelector('#form-member').getAttribute('data-bs-phone') : '');
    $('#member-address').val(isMe ? document.querySelector('#form-member').getAttribute('data-bs-address') : '');
    $('#member-postal-code').val(isMe ? document.querySelector('#form-member').getAttribute('data-bs-postal-code') : '');
    $('#member-city').val(isMe ? document.querySelector('#form-member').getAttribute('data-bs-city') : '');
  });
  const passSwitch = document.querySelector('#pass-switch');
  passSwitch.addEventListener('change', () => {
    $('#pass-div').attr('hidden', !$('#pass-switch').is(':checked'));
    if (!$('#pass-switch').is(':checked')) {
      $('#member-pass-code').val('');
    }
  });
}

function getAge(birthday) {
  const today = new Date();
  const birthDate = new Date(birthday);
  const yearsDifference = today.getFullYear() - birthDate.getFullYear();
  const isBeforeBirthday =
    today.getMonth() < birthDate.getMonth() ||
    (today.getMonth() === birthDate.getMonth() &&
      today.getDate() < birthDate.getDate());
  return isBeforeBirthday ? yearsDifference - 1 : yearsDifference;
};

function majorityImpact(isMajor) {
  if (isMajor) {
    $('#emergency').addClass('d-none');
    $('#contact-responsible-div').addClass('d-none');
  } else {
    $('#emergency').removeClass('d-none');
    $('#contact-responsible-div').removeClass('d-none');
  }
}

function getCurrentSeason() {
  return $.ajax({
    url: seasonsUrl + '?is_current=True',
    type: 'GET',
  });
}

function getCourses() {
  return getCurrentSeason().then(data => {
    const seasonId = data[0].id;
    $.ajax({
      url: coursesUrl + `?season=${seasonId}`,
      type: 'GET',
      success: (data) => {
        let memberCourses = document.querySelector('#member-courses');
        memberCourses.innerHTML = '';
        data.map((course) => {
          const startHour = course.start_hour.split(':');
          const endHour = course.end_hour.split(':');
          const label = `${course.name} - ${WEEKDAY[course.weekday]}, ${startHour[0]}h${startHour[1]} à ${endHour[0]}h${endHour[1]} - ${course.price}€`;
          memberCourses.innerHTML += `<div class="form-check">
  <input class="form-check-input course-checkbox" type="checkbox" value="${course.id}" id="check-${course.id}">
  <label class="form-check-label" for="check-${course.id}">${label}</label>
</div>
`
        });
      },
      error: (error) => {
        showToast('Impossible de récupérer les cours de la saison.');
        console.log(error);
      }
    });
    let memberSeason = $('#member-season');
    memberSeason.append($('<option>', { value: seasonId, text: data[0].year }));
    memberSeason.val(seasonId)
  }).catch(error => {
    showToast('Impossible de récupérer la saison en cours.');
    console.log(error);
  });
}

function createUpdateMember() {
  $('#form-member').submit((event) => {
    event.preventDefault();
    const url = $('#form-member').data('url');
    const method = $('#form-member').data('method');
    console.log(url, method)
    postOrPatchMember(url, method, event);
  })
}

function getMember() {
  getCourses().then(() => {
    var urlParams = new URLSearchParams(window.location.search);
    let member;
    var isEdition = true;
    if (urlParams.get('from_pk') !== null) {
      member = urlParams.get('from_pk');
      $('#form-member').data('url', membersUrl);
      $('#form-member').data('method', 'POST');
      isEdition = false;
    } else if (urlParams.get('pk') !== null) {
      member = urlParams.get('pk');
      $('#form-member').data('url', membersUrl + member + '/');
      $('#form-member').data('method', 'PATCH');
    } else {
      $('h1').html('Ajouter un nouvel adhérent');
      $('#form-member').data('url', membersUrl);
      $('#form-member').data('method', 'POST');
      return
    }
    $.ajax({
      url: membersUrl + member + '/',
      type: 'GET',
      success: (data) => {
        $('#me-switch').prop('disabled', true);
        const action = isEdition ? 'Modifier les infos de' : 'Renouveller' ;
        $('h1').html(`${action} ${data.first_name} ${data.last_name}`);
        $('#member-firstname').val(data.first_name);
        $('#member-lastname').val(data.last_name);
        $('#member-email').val(data.email);
        $('#member-phone').val(data.phone);
        $('#member-address').val(data.address);
        $('#member-postal-code').val(data.postal_code);
        $('#member-city').val(data.city);
        $('#member-birthday').val(data.birthday);
        $('#authorise-photos').prop('checked', isEdition ? data.documents.authorise_photos : true);
        $('#authorise-emergency').prop('checked', isEdition ? data.documents.authorise_emergency : true);
        $('#member-pass-code').val(data.sport_pass?.code || '');
        $('#member-pass-amount').val(data.sport_pass?.amount || 50);
        const withPass = !(data.sport_pass === null || data.sport_pass?.code === null || data.sport_pass?.code === '');
        $('#pass-div').attr('hidden', !withPass);
        $('#pass-switch').prop('checked', withPass);
        document.querySelectorAll('.course-checkbox').forEach(item => {
          isActive = data.active_courses.map(c => c.id.toString()).indexOf(item.value) > -1;
          isWaiting = data.waiting_courses.map(c => c.id.toString()).indexOf(item.value) > -1;
          item.checked = isActive || isWaiting;
          if (isWaiting) {
            label = $(`label[for="${item.id}"]`)[0]
            label.innerHTML += ' <strong>(sur liste d\'attente)</strong>';
          }
        });
        $('#member-license').val(isEdition ? data.ffd_license : 0);
        if (isEdition && data.is_validated) {
          $('#member-courses-accordion').addClass('d-none');
          $('#authorise-photos').prop('disabled', true);
          $('#authorise-emergency').prop('disabled', true);
          $('#member-btn').html('Modifier');
        }
        if (isMe(data)) {
          $('#emergency-me-switch').attr('disabled', true);
          $('#emergency-me-switch').prop('checked', false);
        } else {
          $('#emergency-me-switch').attr('disabled', false);
        }
        const isMajor = Boolean(getAge(data.birthday) >= 18);
        majorityImpact(isMajor);
        Object.keys(CONTACT_MAPPING).forEach(key => {
          $(`#${key}-me-switch`).prop('checked', false);
          const subContacts = data.contacts.filter((c) => c.contact_type === key);
          let delta = 0;
          for (let i = 0; i < CONTACT_ALL_NUMBER; i++) {
            if (i < subContacts.length && isMe(subContacts[i])) {
              $(`#${key}-me-switch`).prop('checked', true);
              delta++;
            } else {
              $(`#firstname-${key}-${i-delta}`).val(i < subContacts.length ? subContacts[i].first_name : '');
              $(`#lastname-${key}-${i-delta}`).val(i < subContacts.length ? subContacts[i].last_name : '');
              $(`#phone-${key}-${i-delta}`).val(i < subContacts.length ? subContacts[i].phone : '');
              $(`#contact-${key}-${i-delta}`).attr('hidden', i-delta > 0 && i-delta >= subContacts.length);
              if (key === 'responsible') {
                $(`#email-${key}-${i-delta}`).val(i < subContacts.length ? subContacts[i].email : '');
              }
            }
          }
        });
      },
      error: (error) => {
        showToast('Impossible de récupérer les informations de cet adhérent.');
        console.log(error);
      }
    });
  }).catch(error => {
    showToast('Impossible de récupérer la saison en cours.');
    console.log(error);
  });
}

function isMe(contact) {
  return contact.first_name.toLowerCase() === document.querySelector('#form-member').getAttribute('data-bs-firstname').toLowerCase()
  && contact.last_name.toLowerCase() === document.querySelector('#form-member').getAttribute('data-bs-lastname').toLowerCase()
}

function postOrPatchMember(url, method, event) {
    $('.invalid-feedback').removeClass('d-inline');
    $('#message-error-contact').addClass('d-none');
    let data = {
      first_name: $('#member-firstname').val(),
      last_name: $('#member-lastname').val(),
      email: $('#member-email').val(),
      phone: $('#member-phone').val(),
      address: $('#member-address').val(),
      postal_code: $('#member-postal-code').val(),
      city: $('#member-city').val(),
      birthday: $('#member-birthday').val(),
      season: $('#member-season').val(),
      ffd_license: $('#member-license').val(),
      contacts: buildContactsData(),
      documents: {
        authorise_photos: $('#authorise-photos').is(':checked'),
        authorise_emergency: $('#authorise-emergency').is(':checked'),
      }
    };
    let courses = [];
    document.querySelectorAll('.course-checkbox').forEach(item => {
      if (item.checked) {
        courses.push(item.value);
      }
    });
    data.active_courses = courses;
    if ($('#member-pass-code').val() !== '') {
      data.sport_pass = { code: $('#member-pass-code').val() };
    }
    $.ajax({
      url: url,
      type: method,
      contentType: 'application/json',
      headers: { 'X-CSRFToken': csrftoken },
      mode: 'same-origin',
      data: JSON.stringify(data),
      dataType: 'json',
      success: () => {
        window.location.replace('/');
      },
      error: (error) => {
        if (!error.responseJSON) {
          showToast('Une erreur est survenue lors de l\'enregistrement du membre.');
        } else {
          const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('member-error-toast'));
          let message = 'Certaines informations sont manquantes ou erronées. Veuillez vérifier les différents champs.';
          if (error.responseJSON.contacts) {
            message += ' Il y a notamment un souci au niveau des contacts.';
          }
          $('#member-error-body').text(message);
          toast.show();
        }
        if (error.responseJSON && error.responseJSON.first_name) {
          $('#invalid-member-first-name').html(error.responseJSON.first_name[0]);
          $('#invalid-member-first-name').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.last_name) {
          $('#invalid-member-last-name').html(error.responseJSON.last_name[0]);
          $('#invalid-member-last-name').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.birthday) {
          $('#invalid-member-birthday').html('Veuillez saisir une date valide.');
          $('#invalid-member-birthday').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.address) {
          $('#invalid-member-address').html(error.responseJSON.address[0]);
          $('#invalid-member-address').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.postal_code) {
          $('#invalid-member-postal-code').html(error.responseJSON.postal_code[0]);
          $('#invalid-member-postal-code').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.city) {
          $('#invalid-member-city').html(error.responseJSON.city[0]);
          $('#invalid-member-city').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.email) {
          $('#invalid-member-email').html(error.responseJSON.email[0]);
          $('#invalid-member-email').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.phone) {
          $('#invalid-member-phone').html(error.responseJSON.phone[0] + ' Format attendu: 0123456789.');
          $('#invalid-member-phone').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.active_courses) {
          $('#invalid-member-courses').html(error.responseJSON.active_courses[0]);
          $('#invalid-member-courses').addClass('d-inline');
        }
        if (error.responseJSON && error.responseJSON.contacts) {
          $('#message-error-contact').removeClass('d-none');
        }
      }
  });
}

function buildContactsData() {
  let contacts = [];
  const isMajor = Boolean(getAge($('#member-birthday').val()) >= 18);
  if (!isMajor) {
    if ($('#responsible-me-switch').is(':checked')) {
      contacts.push({
        first_name: document.querySelector('#form-member').getAttribute('data-bs-firstname'),
        last_name: document.querySelector('#form-member').getAttribute('data-bs-lastname'),
        phone: document.querySelector('#form-member').getAttribute('data-bs-phone'),
        email: document.querySelector('#form-member').getAttribute('data-bs-email'),
        contact_type: 'responsible',
      });
    }
    for (let i = 0; i < CONTACT_CUSTOM_NUMBER; i++) {
      if ($(`#firstname-responsible-${i}`).val() !== '') {
        contacts.push({
          first_name: $(`#firstname-responsible-${i}`).val(),
          last_name: $(`#lastname-responsible-${i}`).val(),
          phone: $(`#phone-responsible-${i}`).val(),
          email: $(`#email-responsible-${i}`).val(),
          contact_type: 'responsible',
        });
      }
    }
  }

  if ($('#emergency-me-switch').is(':checked')) {
    contacts.push({
      first_name: document.querySelector('#form-member').getAttribute('data-bs-firstname'),
      last_name: document.querySelector('#form-member').getAttribute('data-bs-lastname'),
      phone: document.querySelector('#form-member').getAttribute('data-bs-phone'),
      email: undefined,
      contact_type: 'emergency',
    });
  }
  for (let i = 0; i < CONTACT_CUSTOM_NUMBER; i++) {
    if ($(`#firstname-emergency-${i}`).val() !== '') {
      contacts.push({
        first_name: $(`#firstname-emergency-${i}`).val(),
        last_name: $(`#lastname-emergency-${i}`).val(),
        phone: $(`#phone-emergency-${i}`).val(),
        email: undefined,
        contact_type: 'emergency',
      });
    }
  }
  return contacts
}

function initContacts() {
  const emergencyParent = document.querySelector('#contact-emergency-div');
  const responsibleParent = document.querySelector('#contact-responsible-div');
  const contactTemplate = document.querySelector('#contact-template');
  for (let i = 0; i < CONTACT_CUSTOM_NUMBER; i++) {
    Object.keys(CONTACT_MAPPING).forEach(key => {
      const clone = contactTemplate.content.cloneNode(true);
      const items = clone.querySelectorAll('.form-outline');
      for (let k = 0; k < items.length; k++) {
        // No email for emergency contacts
        if (key === 'emergency' && k === items.length - 1) {
          items[k].parentElement.remove();
        } else {
          items[k].children[0].htmlFor += `${key}-${i}`;
          items[k].children[1].id += `${key}-${i}`;
          // For invalid feedbacks
          if (items[k].children.length > 2) {
            items[k].children[2].id += `${key}-${i}`;
          }
        }
      }
      // Add button except for last
      if (i < CONTACT_CUSTOM_NUMBER - 1) {
        const addTemplate = document.querySelector('#add-contact-template');
        const addClone = addTemplate.content.cloneNode(true);
        let addContactButton = addClone.querySelector('button');
        addContactButton.id += `add-contact-${key}-${i}`;
        clone.querySelector('.row').appendChild(addClone);
      }
      // Delete button + hidden except for first
      if (i > 0) {
        const removeTemplate = document.querySelector('#remove-contact-template');
        const removeClone = removeTemplate.content.cloneNode(true);
        let removeContactButton = removeClone.querySelector('button');
        removeContactButton.id += `remove-contact-${key}-${i}`;
        removeContactButton.dataset.bsEnumber = i;
        clone.querySelector('.row').appendChild(removeClone);
        clone.querySelectorAll('div')[0].id = `contact-${key}-${i}`;
        clone.querySelectorAll('div')[0].hidden = true;
      }
      if (key === 'emergency') {
        emergencyParent.appendChild(clone);
      } else {
        responsibleParent.appendChild(clone);
      }
    });
  }
}

function handleContacts() {
  Object.keys(CONTACT_MAPPING).forEach(key => {
    for (let i = 0; i < CONTACT_CUSTOM_NUMBER - 1; i++) {
      $(`#add-contact-${key}-${i}`).on('click', () => {
        $(`#contact-${key}-${i + 1}`).attr('hidden', false);
      });
    }
    for (let i = 1; i < CONTACT_CUSTOM_NUMBER; i++) {
      $(`#remove-contact-${key}-${i}`).on('click', () => {
        ['firstname', 'lastname', 'phone', 'email'].forEach(item => {
          $(`#${item}-${key}-${i}`).val('');
        });
        $(`#contact-${key}-${i}`).attr('hidden', true);
      });
    }
  });
  ['firstname', 'lastname'].forEach(name => {
    $(`#member-${name}`).change(function () {
      const isMeMember = isMe({first_name: $('#member-firstname').val(), last_name: $('#member-lastname').val()});
      $('#emergency-me-switch').attr('disabled', isMeMember);
      $('#emergency-me-switch').prop('checked', !isMeMember);
    });
  });
}

function showToast(text) {
  const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('member-error-toast'));
  $('#member-error-body').text(`${text} ${ERROR_SUFFIX}`);
  toast.show();
}
