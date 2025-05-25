$(document).ready(() => {
	initialize();
});

async function initialize() {
	if (sessionStatus == 'SUCCESSFUL') {
		$('#checkout-success').attr('hidden', false);
		setTimeout(() => { location.href = '/'}, 7000);
	} else if (sessionStatus == 'STATUS_UNKNOWN') {
		$('#checkout-unknown').attr('hidden', false);
		setTimeout(() => { location.href = '/'}, 10000);
	} else {
		$('#checkout-failure').attr('hidden', false);
		setTimeout(() => { location.href = '/checkout'}, 7000);
	}
}
