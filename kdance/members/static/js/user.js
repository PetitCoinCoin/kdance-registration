$(document).ready(() => {
    getUser();
    patchUser();
});

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
            $('#desc-picture').attr('src', `https://api.dicebear.com/8.x/thumbs/svg?seed=${data.username}`);
            $('#edit-me-firstname').val(data.first_name);
            $('#edit-me-lastname').val(data.last_name);
            $('#edit-me-username').val(data.username);
            $('#edit-me-email').val(data.email);
            $('#edit-me-phone').val(data.profile.phone);
            $('#edit-me-address').val(data.profile.address);
            const accordionParent = document.querySelector('#member-accordion');
            const accordionTemplate = document.querySelector('#accordion-item-template');
            const cardTemplate = document.querySelector('#card-template');
            data.payment.map((item, i) => {
                const season_members = data.members.filter((m) => {
                    return m.courses.filter((c) => {return c.season === item.season}).length > 0
                });

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
                let collapsing = clone.querySelectorAll('div.accordion-collapse')[0];
                collapsing.id = `accordion-${i}`;
                // collapse older seasons
                if (i > 0) {
                    collapseBtn.ariaExpanded = false;
                    collapseBtn.classList.add('collapsed');
                    collapsing.classList.remove('show');
                }
                // Member info
                let body = clone.querySelectorAll('div.accordion-body')[0];
                season_members.map((member) => {
                    const cardClone = cardTemplate.content.cloneNode(true);
                    let memberTitle = cardClone.querySelectorAll('div.card-header')[0];
                    memberTitle.textContent = `${member.first_name} ${member.last_name}`;
                    let memberBody = cardClone.querySelectorAll('div.card-body')[0];
                    member.courses.map((course) => {
                        let paragraphe = document.createElement('p');
                        const startHour = course.start_hour.split(':');
                        paragraphe.textContent = `${course.name}, ${WEEKDAY[course.weekday]} ${startHour[0]}h${startHour[1]}`;
                        memberBody.appendChild(paragraphe);
                    });
                    body.appendChild(cardClone);
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