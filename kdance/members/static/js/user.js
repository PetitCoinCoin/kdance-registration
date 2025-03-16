$(document).ready(() => {
  displayPwdToast();
  activatePopovers();
  populateLicense();
  getUser();
  getCourses();
  createUpdateMember();
  deleteItem();
  initContacts();
  handleContacts();
  handleSwitches();
  validateMembers();
  const birthdaySelect = document.querySelector('#member-birthday');
  birthdaySelect.addEventListener('change', () => {
    const isMajor = Boolean(getAge($('#member-birthday').val()) >= 18);
    majorityImpact(isMajor);
  });
});


function displayPwdToast() {
  if (window.location.hash === '#pwd_ok') {
    const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('pwd-success-toast'));
    toast.show();
    window.location.hash = '';
  }
}

function activatePopovers() {
  const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
  [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
}

function handleSwitches() {
  const meSwitch = document.querySelector('#me-switch');
  meSwitch.addEventListener('change', () => {
    const isMe = $('#me-switch').is(':checked');
    $('#member-email').val(isMe ? $('#desc-email').html() : '');
    $('#member-phone').val(isMe ? $('#desc-phone').html() : '');
    $('#member-address').val(isMe ? $('#desc-address').html() : '');
  });
  const passSwitch = document.querySelector('#pass-switch');
  passSwitch.addEventListener('change', () => {
    $('#pass-div').attr('hidden', !$('#pass-switch').is(':checked'));
  });
}

function getPreviousMembers(members) {
  let previousMembers = new Array
  members.map((m) => {
    let found = false;
    let removeIndex = undefined;
    for (var i = 0; i < previousMembers.length; i++) {
      pm = previousMembers[i]
      if (pm.first_name === m.first_name && pm.last_name === m.last_name) {
        found = true;
        if (m.season.year > pm.season.year) {
          removeIndex = i;
        }
        break;
      }
    }
    if (!found) {
      previousMembers.push(m);
    } else if (removeIndex !== undefined) {
      previousMembers.splice(removeIndex, 1);
      previousMembers.push(m);
    }
  })
  return previousMembers
}

function populateDocuments(member, memberInfos) {
  const docTemplate = document.querySelector('#member-doc-template');
  const clone = docTemplate.content.cloneNode(true);
  let icons = clone.querySelectorAll('i');
  let liItems = clone.querySelectorAll('li');
  icons[0].className = member.documents?.authorise_photos ? 'bi-check-circle-fill' : 'bi-x-circle-fill';
  icons[0].style = member.documents?.authorise_photos ? 'color: #baffc9;' : 'color: #ffb3ba;';
  icons[1].className = member.documents?.authorise_emergency ? 'bi-check-circle-fill' : 'bi-x-circle-fill';
  icons[1].style = member.documents?.authorise_emergency ? 'color: #baffc9;' : 'color: #ffb3ba;';
  const medicalDocStatus = Boolean(member.documents != undefined && member.documents.medical_document !== 'Manquant')
  icons[2].className = medicalDocStatus ? 'bi-check-circle-fill' : 'bi-x-circle-fill';
  icons[2].style = medicalDocStatus ? 'color: #baffc9;' : 'color: #ffb3ba;';
  const doc = member.documents?.medical_document || '';
  liItems[2].innerHTML += `Document médical: ${doc} ${
    doc === 'Manquant' || doc === ''
    ? buildHelper('Vous pourrez apporter votre attestation ou votre certificat médical lors du forum ou des permanences. Vous pourrez également les faire passer lors des cours ou par email à kdance31340@gmail.com')
    : ''}`;
  const isMajor = Boolean(getAge(member.birthday) >= 18);
  if (isMajor) {
    liItems[1].remove()
  }
  memberInfos.appendChild(clone);
}

function populateLicense() {
  for (let [key, value] of Object.entries(LICENSES)) {
    const label = key === '0' ? value : `${value} (${key}€)`;
    $('#member-license').append($('<option>', { value: key, text: label, selected: key == '0' }));
  }
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

function getUser() {
  $.ajax({
    url: userMeUrl,
    type: 'GET',
    success: (data) => {
      $('#desc-firstname').html(data.first_name);
      $('#desc-lastname').html(data.last_name);
      $('#desc-email').html(data.email);
      $('#desc-phone').html(data.profile.phone);
      $('#desc-address').html(data.profile.address);
      $('#desc-picture').attr('src', `https://api.dicebear.com/8.x/thumbs/svg?seed=${data.first_name + data.last_name}`);
      const accordionParent = document.querySelector('#member-accordion');
      const accordionTemplate = document.querySelector('#accordion-item-template');
      const cardTemplate = document.querySelector('#card-template');
      const memberBtnTemplate = document.querySelector('#member-btn-template');
      // Previous seasons members
      const previousMembers = getPreviousMembers(data.members.filter((m) => !m.season.is_current));
      let memberSelect = $('#copy-member-select');
      previousMembers.map((m) => {
        memberSelect.append($('<option>', { value: m.id, text: `${m.first_name} ${m.last_name}` }));
      })
      data.payment.sort(
        (a,b) => (a.season.year < b.season.year) ? 1 : ((b.season.year < a.season.year) ? -1 : 0)
      ).map((item, i) => {
        const clone = accordionTemplate.content.cloneNode(true);
        // Payment info
        let title = clone.querySelector('span');
        title.textContent = `Saison ${item.season.year}`;
        let dd = clone.querySelectorAll('dd.payment');
        let details = 'Details:<br />- ' + item.due_detail.join('<br />- ');
        dd[0].innerHTML = `${item.due}€ ${item.due > 0 ? buildHelper(details) : ''}`;
        dd[1].innerHTML = `${item.paid}€`;
        dd[2].innerHTML = `${item.refund}€`;
        // Collapsible
        let collapseBtn = clone.querySelector('button');
        collapseBtn.dataset.bsTarget = `#accordion-${i}`;
        collapseBtn.ariaControls = `accordion-${i}`;
        let collapsing = clone.querySelector('div.accordion-collapse');
        collapsing.id = `accordion-${i}`;
        // collapse older seasons and add member button for current season
        if (i > 0) {
          collapseBtn.ariaExpanded = false;
          collapseBtn.classList.add('collapsed');
          collapsing.classList.remove('show');
        } else {
          const memberBtnClone = memberBtnTemplate.content.cloneNode(true);
          if (previousMembers.length == 0) {
            let copyBtn = memberBtnClone.querySelector('#copy-member-btn');
            copyBtn.remove();
          }
          const btnParent = clone.querySelector('.season-btn-div');
          if (data.members.filter((member) => member.season.id == item.season.id && !member.is_validated).length == 0) {
            memberBtnClone.querySelector('#validate-members-btn').disabled = true;
          }
          btnParent.appendChild(memberBtnClone);
        }
        // Member info
        let body = clone.querySelector('div.accordion-body');
        data.members.map((member) => {
          if (member.season.id === item.season.id) {
            const cardClone = cardTemplate.content.cloneNode(true);
            let memberTitle = cardClone.querySelector('span');
            memberTitle.textContent = `${member.first_name} ${member.last_name}`;
            let avatar = cardClone.querySelector('img');
            avatar.src = `https://api.dicebear.com/8.x/thumbs/svg?seed=${member.first_name + member.last_name}&radius=50`;
            let editButton = cardClone.querySelector('.m-edit-btn');
            editButton.dataset.bsMid = member.id;
            let deleteButton = cardClone.querySelector('.m-delete-btn');
            deleteButton.dataset.bsMid = member.id;
            deleteButton.dataset.bsMname = `${member.first_name} ${member.last_name}`;
            if (!item.season.is_current) {
              editButton.remove();
              deleteButton.remove();
            } else if (member.is_validated) {
              deleteButton.remove();
            }
            let memberInfos = cardClone.querySelector('ul');
            member.active_courses.map((course) => {
              let liItem = document.createElement('li');
              liItem.className = 'list-group-item';
              const startHour = course.start_hour.split(':');
              liItem.textContent = `${course.name}, ${WEEKDAY[course.weekday]} ${startHour[0]}h${startHour[1]}`;
              memberInfos.appendChild(liItem);
            })
            member.cancelled_courses.map((course) => {
              let liItem = document.createElement('li');
              liItem.className = 'list-group-item fst-italic';
              const startHour = course.start_hour.split(':');
              liItem.textContent = `(Annulé) ${course.name}, ${WEEKDAY[course.weekday]} ${startHour[0]}h${startHour[1]}`;
              memberInfos.appendChild(liItem);
            })
            populateDocuments(member, memberInfos);
            body.appendChild(cardClone);
          }
        });
        accordionParent.appendChild(clone);
        activatePopovers();
      })
    },
    error: (error) => {
      showToast('Impossible de récupérer vos informations pour le moment.');
      console.log(error);
    }
  });
}

function getCurrentSeason() {
  return $.ajax({
    url: seasonsUrl + '?is_current=True',
    type: 'GET',
  });
}

function getCourses() {
  getCurrentSeason().then(data => {
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
  const memberModal = document.getElementById('member-modal');
  if (memberModal) {
    $('#member-modal').on('show.bs.modal', function(event) {
      // Reset accordion collapsed items and focus
      $('.invalid-feedback').removeClass('d-inline');
      ['contact', 'courses', 'authorise'].forEach(item => {
        $(`#member-${item}-section`).removeClass('show');
        $(`#member-${item}-section`).addClass('collapsed');
        const headerButton = $(`*[data-bs-target="#member-${item}-section"]`)
        headerButton.addClass('collapsed');
        headerButton.attr('aria-expanded', false);
      });
      $('#member-info-section').removeClass('collapsed');
      $('#member-info-section').addClass('show');
      const headerButton =  $('*[data-bs-target="#member-info-section"]');
      headerButton.removeClass('collapsed');
      headerButton.attr('aria-expanded', true);
      // Handle data
      const button = event.relatedTarget;
      const member = button.getAttribute('data-bs-mid');
      let url = membersUrl;
      let method = 'POST';
      if (member === null) {
        // Create member
        buttonId = button.getAttribute('id');
        $('#member-courses-accordion').removeClass('d-none');
        $('#authorise-photos').prop('disabled', false);
        $('#authorise-emergency').prop('disabled', false);
        if (buttonId === 'copy-btn') {
          // From previous member
          getMember($('#copy-member-select').val(), false);
        } else {
          // From scratch
          cleanMemberForm();
        }
        $('#member-btn').html('Ajouter');
      } else {
        // Update member
        getMember(member, true);
        url = url + member + '/';
        method = 'PATCH';
      }
      $('#form-member').data('url', url);
      $('#form-member').data('method', method);
    });
    $('#member-modal').on('submit', '#form-member', function(event) {
      event.preventDefault();
      const url = $(this).data('url');
      const method = $(this).data('method');
      postOrPatchMember(url, method, event);
    })
  }
}

function cleanMemberForm() {
  $('.invalid-feedback').removeClass('d-inline');
  $('#me-switch').prop('disabled', false);
  $('#me-switch').prop('checked', false);
  $('#member-modal-title').html('Ajouter un nouvel adhérent');
  $('#member-firstname').val(undefined);
  $('#member-lastname').val(undefined);
  $('#member-email').val(undefined);
  $('#member-phone').val(undefined);
  $('#member-address').val(undefined);
  $('#member-birthday').val(undefined);
  document.querySelectorAll('.course-checkbox').forEach(item => item.checked = false);
  $("#member-license").val(0);
}

function getMember(member, isEdition) {
  $.ajax({
    url: membersUrl + member + '/',
    type: 'GET',
    success: (data) => {
      $('#me-switch').prop('disabled', true);
      const action = isEdition ? 'Modifier' : 'Copier';
      $('#member-modal-title').html(`${action} les informations de ${data.first_name} ${data.last_name}`);
      $('#member-firstname').val(data.first_name);
      $('#member-lastname').val(data.last_name);
      $('#member-email').val(data.email);
      $('#member-phone').val(data.phone);
      $('#member-address').val(data.address);
      $('#member-birthday').val(data.birthday);
      $('#authorise-photos').prop('checked', isEdition ? data.documents.authorise_photos : true);
      $('#authorise-emergency').prop('checked', isEdition ? data.documents.authorise_emergency : true);
      $('#member-pass-code').val(data.sport_pass?.code || '');
      $('#member-pass-amount').val(data.sport_pass?.amount || 50);
      const withPass = !(data.sport_pass === null || data.sport_pass?.code === null || data.sport_pass?.code === '');
      $('#pass-div').attr('hidden', !withPass);
      $('#pass-switch').prop('checked', withPass);
      document.querySelectorAll('.course-checkbox').forEach(item => {
        item.checked = data.active_courses.map(c => c.id.toString()).indexOf(item.value) > -1;
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
}

function isMe(contact) {
  return contact.first_name.toLowerCase() === $('#desc-firstname').html().toLowerCase()
  && contact.last_name.toLowerCase() === $('#desc-lastname').html().toLowerCase()
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
      data.sport_pass = {
        code: $('#member-pass-code').val(),
        amount: $('#member-pass-amount').val(),
      };
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
        event.currentTarget.submit();
      },
      error: (error) => {
        if (!error.responseJSON) {
          showToast('Une erreur est survenue lors de l\'enregistrement du membre.');
          console.log(error);
        } else {
          const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('user-error-toast'));
          let message = 'Certaines informations sont manquantes ou erronées. Veuillez vérifier les différents champs.';
          if (error.responseJSON.contacts) {
            message += ' Il y a notamment un souci au niveau des contacts.';
          }
          $('#user-error-body').text(message);
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
        first_name: $('#desc-firstname').html(),
        last_name: $('#desc-lastname').html(),
        phone: $('#desc-phone').html(),
        email: $('#desc-email').html(),
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
      first_name: $('#desc-firstname').html(),
      last_name: $('#desc-lastname').html(),
      phone: $('#desc-phone').html(),
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

function deleteItem() {
  const deleteModal = document.getElementById('delete-modal');
  if (deleteModal) {
    deleteModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const buttonId = button.getAttribute('id');
      const buttonClass = button.getAttribute('class');
      const modalBody = deleteModal.querySelector('.modal-body');
      let url = '';
      let errorMessage = '';
      if (buttonId === 'delete-me-btn') {
        $('#delete-modal-title').html('Supprimer mon compte');
        modalBody.textContent = 'Etes-vous sur.e de vouloir supprimer votre compte ainsi que tous les adhérents associés ?';
        url = userMeUrl;
        errorMessage = 'Une erreur est survenue, impossible de supprimer le compte pour le moment.';
      }
      else if (buttonClass.includes('m-delete-btn')) {
        $('#delete-modal-title').html('Supprimer un adhérent');
        const memberId = button.getAttribute('data-bs-mid');
        const member = button.getAttribute('data-bs-mname');
        modalBody.textContent = `Etes-vous sur.e de vouloir supprimer ${member} pour cette saison ?`;
        url = membersUrl + memberId + '/';
        errorMessage = 'Une erreur est survenue, impossible de supprimer cet adhérent pour le moment.';
      }
      $(document).on("click", "#delete-btn", function () {
        $.ajax({
          url: url,
          type: 'DELETE',
          headers: { 'X-CSRFToken': csrftoken },
          mode: 'same-origin',
          success: () => {
            location.reload();
          },
          error: (error) => {
            showToast(errorMessage);
            console.log(error);
          }
        });
      });
    });
  }
}

function validateMembers() {
  const validateModal = document.getElementById('validate-modal');
  if (validateModal) {
    validateModal.addEventListener('show.bs.modal', event => {
      $(document).on("click", "#validate-btn", function () {
        $.ajax({
          url: userMeValidateUrl,
          type: 'PUT',
          headers: { 'X-CSRFToken': csrftoken },
          mode: 'same-origin',
          success: () => {
            location.reload();
          },
          error: (error) => {
            showToast(errorMessage);
            console.log(error);
          }
        });
      });
    });
  }
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
  const toast = bootstrap.Toast.getOrCreateInstance(document.getElementById('user-error-toast'));
  $('#user-error-body').text(`${text} ${ERROR_SUFFIX}`);
  toast.show();
}

function buildHelper(text) {
  return `
<span tabindex="0" data-bs-toggle="popover" data-bs-trigger="hover focus" data-bs-content="${text}" data-bs-placement="right" data-bs-html="true">
  <i class="bi-info-circle main-blue"></i>
</span>
`
}
