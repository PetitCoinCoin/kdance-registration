$(document).ready(() => {
	initialize();
});

async function initialize() {
	if (sessionStatus == 'complete') {
		$('#checkout-success').attr('hidden', false);
		setTimeout(() => { location.href = '/'}, 10000);
	} else {
		$('#checkout-failure').attr('hidden', false);
		setTimeout(() => { location.href = '/checkout'}, 10000);
	}
}
