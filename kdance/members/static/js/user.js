$(document).ready(() => {
    getUser();
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
                title.textContent = `Saison ${item.season}`;
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
                        paragraphe.textContent = `${course.name}, ${course.weekday} ${startHour[0]}h${startHour[1]}`;
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
