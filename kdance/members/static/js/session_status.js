$(document).ready(() => {
	initialize();
});

async function initialize() {
	if (sessionStatus == 'SUCCESSFUL') {
		$('#checkout-success').attr('hidden', false);
		setTimeout(() => { location.href = '/'}, 7000);
	} else {
		$('#checkout-failure').attr('hidden', false);
		setTimeout(() => { location.href = '/checkout'}, 7000);
	}
}
