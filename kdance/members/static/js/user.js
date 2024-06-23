$(document).ready(() => {
  getUser();
  patchUser();
  getCourses();
  createUpdateMember();
  deleteItem();
  const meSwitch = document.querySelector('#me-switch');
  meSwitch.addEventListener('change', () => {
    const isMe = $('#me-switch').is(':checked');
    $('#member-firstname').val(isMe ? $('#desc-firstname').html() : ''),
    $('#member-lastname').val(isMe ? $('#desc-lastname').html() : ''),
    $('#member-email').val(isMe ? $('#desc-email').html() : ''),
    $('#member-phone').val(isMe ? $('#desc-phone').html() : ''),
    $('#member-address').val(isMe ? $('#desc-address').html() : '')
  });
  const birthdaySelect = document.querySelector('#member-birthday');
  birthdaySelect.addEventListener('change', () => {
    const isMajor = Boolean(getAge($('#member-birthday').val()) >= 18);
    if (isMajor) {
      $('#emergency').addClass('d-none');
    } else {
      $('#emergency').removeClass('d-none');
    }
 });
});

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
  liItems[2].innerHTML += `Document médical: ${member.documents?.medical_document}`;
  memberInfos.appendChild(clone);
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

function getUser() {
    $.ajax({
        url: userMeUrl,
        type: 'GET',
        success: (data) => {
            $('#desc-firstname').html(data.first_name);
            $('#desc-lastname').html(data.last_name);
            $('#desc-username').html(data.username);
            $('#desc-email').html(data.email);
            $('#desc-phone').html(data.profile.phone);
            $('#desc-address').html(data.profile.address);
            $('#desc-picture').attr('src', `https://api.dicebear.com/8.x/thumbs/svg?seed=${data.first_name + data.last_name}`);
            $('#edit-me-firstname').val(data.first_name);
            $('#edit-me-lastname').val(data.last_name);
            $('#edit-me-username').val(data.username);
            $('#edit-me-email').val(data.email);
            $('#edit-me-phone').val(data.profile.phone);
            $('#edit-me-address').val(data.profile.address);
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
            data.payment.map((item, i) => {
                const clone = accordionTemplate.content.cloneNode(true);
                // Payment info
                let title = clone.querySelector('span');
                title.textContent = `Saison ${item.season.year}`;
                let dd = clone.querySelectorAll('dd.payment');
                dd[0].textContent = `${item.due}€`;
                dd[1].textContent = `${item.paid}€`;
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
                  const btnParent = clone.querySelector('div.accordion-body').children[0];
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
                      let button = cardClone.querySelector('button');
                      button.dataset.bsMid = member.id;
                      if (!item.season.is_current) {
                        button.remove();
                      }
                      let memberInfos =  cardClone.querySelector('ul');
                      member.courses.map((course) => {
                        let liItem = document.createElement('li');
                        liItem.className = 'list-group-item';
                        const startHour = course.start_hour.split(':');
                        liItem.textContent = `${course.name}, ${WEEKDAY[course.weekday]} ${startHour[0]}h${startHour[1]}`;
                        memberInfos.appendChild(liItem);
                      })
                      populateDocuments(member, memberInfos);
                      body.appendChild(cardClone);
                    }
                });
                accordionParent.appendChild(clone);
            })
        },
        error: (error) => {
            // if (!error.responseJSON) {
            //     $('#message-error-signup').removeAttr('hidden');
            // }
        }
    });
}

function patchUser() {
    $('#form-me').submit((event) => {
        $('.invalid-feedback').removeClass('d-inline');
        event.preventDefault();
        const data = {
          first_name: $('#edit-me-firstname').val(),
          last_name: $('#edit-me-lastname').val(),
          username: $('#edit-me-username').val(),
          email: $('#edit-me-email').val(),
          profile: {
            phone: $('#edit-me-phone').val(),
            address: $('#edit-me-address').val(),
          }
        };
        $.ajax({
          url: userMeUrl,
          type: 'PATCH',
          contentType: 'application/json',
          headers: { 'X-CSRFToken': csrftoken },
          mode: 'same-origin',
          data: JSON.stringify(data),
          dataType: 'json',
          success: () => {
            // Check pwd update
            event.currentTarget.submit();
          },
          error: (error) => {
            if (!error.responseJSON) {
            //   $('#message-error-signup').removeAttr('hidden');
            }
            if (error.responseJSON.username) {
              $('#invalid-edit-me-username').html(error.responseJSON.username[0]);
              $('#invalid-edit-me-username').addClass('d-inline');
            }
            if (error.responseJSON.phone) {
              $('#invalid-edit-me-phone').html(error.responseJSON.phone[0]);
              $('#invalid-edit-me-phone').addClass('d-inline');
            }
            if (error.responseJSON.email) {
              $('#invalid-edit-me-email').html(error.responseJSON.email[0]);
              $('#invalid-edit-me-email').addClass('d-inline');
            }
          }
        });
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
        let memberCourses = $('#member-courses');
        data.map((course) => {
          const label = `${course.name} - ${course.price}€`;
          memberCourses.append($('<option>', { value: course.id, text: label }));
        });
      },
      error: (error) => {
        // if (!error.responseJSON) {
        //     $('#message-error-signup').removeAttr('hidden');
        // }
      }
    });
    let memberSeason = $('#member-season');
    memberSeason.append($('<option>', { value: seasonId, text: data[0].year }));
    memberSeason.val(seasonId)
  }).catch(error => console.log(error));
}

function createUpdateMember() {
  const memberModal = document.getElementById('member-modal');
  if (memberModal) {
    memberModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const member = button.getAttribute('data-bs-mid');
      let url = membersUrl;
      let method = 'POST';
      if (member === null) {
        // Create member
        buttonId = button.getAttribute('id');
        $('#form-member-courses').removeClass('d-none');
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
        $('#form-member-courses').addClass('d-none');
        $('#authorise-photos').prop('disabled', true);
        $('#authorise-emergency').prop('disabled', true);
        $('#membre-btn').html('Modifier');
        url = url + member + '/';
        method = 'PATCH';
      }
      postOrPatchMember(url, method);
    });
  }
}

function cleanMemberForm() {
  $('#me-switch').prop('disabled', false);
  $('#member-modal-title').html('Ajouter un nouveau membre');
  $('#member-firstname').val(undefined);
  $('#member-lastname').val(undefined);
  $('#member-email').val(undefined);
  $('#member-phone').val(undefined);
  $('#member-address').val(undefined);
  $('#member-birthday').val(undefined);
  $("#member-courses").val(undefined);
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
      $('#authorise-emergency').prop('checked', isEdition ? data.documents.authorise_emergency: true);
      if (isEdition) {
        $("#member-courses").val(data.courses.map((c) => c.id));
      }
      const isMajor = Boolean(getAge(data.birthday) >= 18);
      if (isMajor) {
        $('#emergency').addClass('d-none');
      } else {
        $('#emergency').removeClass('d-none');
      }
    },
    error: (error) => {
      // if (!error.responseJSON) {
      //     $('#message-error-signup').removeAttr('hidden');
      // }
    }
  });
}

function postOrPatchMember(url, method) {
  $('#form-member').submit((event) => {
    $('.invalid-feedback').removeClass('d-inline');
    event.preventDefault();
    let data = {
      first_name: $('#member-firstname').val(),
      last_name: $('#member-lastname').val(),
      email: $('#member-email').val(),
      phone: $('#member-phone').val(),
      address: $('#member-address').val(),
      birthday: $('#member-birthday').val(),
      season: $('#member-season').val(),
      courses: $('#member-courses').val(),
      documents: {
        authorise_photos: $('#authorise-photos').is(':checked'),
        authorise_emergency: $('#authorise-emergency').is(':checked'),
      }
    };
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
        // if (!error.responseJSON) {
        //   $('#message-error-signup').removeAttr('hidden');
        // }
      }
    });
  });
}

function deleteItem() {
  const deleteModal = document.getElementById('delete-modal');
  if (deleteModal) {
    deleteModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const buttonId = button.getAttribute('id');
      const modalBody = deleteModal.querySelector('.modal-body');
      let url = '';
      if (buttonId === 'delete-me-btn') {
        $('#delete-modal-title').html('Supprimer mon compte');
        modalBody.textContent = `Etes-vous sur.e de vouloir supprimer votre compte ainsi que tous les membres associés ?`;
        url = userMeUrl;
      }
      $(document).on("click", "#delete-btn", function(){
        $.ajax({
          url: url,
          type: 'DELETE',
          headers: { 'X-CSRFToken': csrftoken },
          mode: 'same-origin',
          success: () => {
            location.reload();
          },
          error: (error) => {
            // if (!error.responseJSON) {
            //   $('#message-error-signup').removeAttr('hidden');
            // }
          }
        });
      });
    });
  }
}
