$(document).ready(() => {
  displayPwdToast();
  activatePopovers();
  getUser();
  deleteMember();
  validateMembers();
  $('#copy-btn').click(() => {
    window.location.href = 'member?' + new URLSearchParams({from_pk: $('#copy-member-select').val()}).toString()
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
      const isPreSignup = new Date(preSignupEnd) >= new Date();
      // Previous seasons members
      const previousMembers = isPreSignup ?
        data.members.filter((m) => m.season.year === previousSeason) :
        getPreviousMembers(data.members.filter((m) => !m.season.is_current));
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
        let details = 'Details:<br />- ' + item.due_detail.join('<br />- ') + '<br />Ne tient pas compte d\'éventuels cours en liste d\'attente';
        dd[0].innerHTML = `${item.due}€ ${item.due > 0 ? buildHelper(details) : ''}`;
        dd[1].innerHTML = `${item.paid}€`;
        dd[2].innerHTML = `${item.refund}€`;
        // Collapsible
        let collapseBtn = clone.querySelector('button');
        collapseBtn.dataset.bsTarget = `#accordion-${i}`;
        collapseBtn.ariaControls = `accordion-${i}`;
        let collapsing = clone.querySelector('div.accordion-collapse');
        collapsing.id = `accordion-${i}`;
        // collapse older seasons and add member buttons for current season
        if (!item.season.is_current) {
          collapseBtn.ariaExpanded = false;
          collapseBtn.classList.add('collapsed');
          collapsing.classList.remove('show');
          const medicalDocDropdown = clone.querySelector('.medical-dropdown');
          medicalDocDropdown.remove();
        } else {
          const memberBtnClone = memberBtnTemplate.content.cloneNode(true);
          if (previousMembers.length == 0) {
            let copyBtn = memberBtnClone.querySelector('#copy-member-btn');
            copyBtn.remove();
          } else if (new Date(item.season.pre_signup_start) > new Date()) {
            let copyBtn = memberBtnClone.querySelector('#copy-member-btn');
            copyBtn.disabled = true;
          }
          const btnParent = clone.querySelector('.season-btn-div');
          const notValidatedMembers = data.members.filter((member) => member.season.id == item.season.id && !member.is_validated);
          if (notValidatedMembers.filter((member) => member.active_courses.length > 0).length == 0) {
            memberBtnClone.querySelector('#checkout-btn').disabled = true;
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
            editButton.onclick = () => {window.location.href = 'member?' + new URLSearchParams({pk: member.id}).toString()}
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
            member.waiting_courses.map((course) => {
              let liItem = document.createElement('li');
              liItem.className = 'list-group-item fst-italic';
              const startHour = course.start_hour.split(':');
              liItem.textContent = `--- Sur liste d'attente: ${course.name}, ${WEEKDAY[course.weekday]} ${startHour[0]}h${startHour[1]} ---`;
              memberInfos.appendChild(liItem);
            })
            member.cancelled_courses.map((course) => {
              let liItem = document.createElement('li');
              liItem.className = 'list-group-item fst-italic';
              const startHour = course.start_hour.split(':');
              liItem.textContent = `(Annulé) ${course.name}, ${WEEKDAY[course.weekday]} ${startHour[0]}h${startHour[1]}`;
              memberInfos.appendChild(liItem);
            })
            if (member.waiting_courses.length) {
              let memberWarning = cardClone.querySelector('p');
              memberWarning.hidden = false;
            }
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

function deleteMember() {
  const deleteModal = document.getElementById('delete-modal');
  if (deleteModal) {
    deleteModal.addEventListener('show.bs.modal', event => {
      const button = event.relatedTarget;
      const modalBody = deleteModal.querySelector('.modal-body');
      $('#delete-modal-title').html('Supprimer un adhérent');
      const memberId = button.getAttribute('data-bs-mid');
      const member = button.getAttribute('data-bs-mname');
      modalBody.textContent = `Etes-vous sur.e de vouloir supprimer ${member} pour cette saison ?`;
      const url = membersUrl + memberId + '/';
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
            const errorMessage = 'Une erreur est survenue, impossible de supprimer cet adhérent pour le moment.';
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
