// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "select2", "touchspin", "icheck"], function(
  $,
  select2,
  touchspin
) {
	"use strict";
	
	let updateFieldsRelatedToNodeType = function(nodeTypeValue) {
		if ($('.js-touchspin-ppn').length > 0) {
			let max = 36;
			if (nodeTypeValue === 'gpu') {
				max = 12;
			}
			$('.js-touchspin-ppn').first().trigger('touchspin.updatesettings', {max: max});
		}
		
		if ($('.js-touchspin-dtaskspn').length > 0) {
			let max = 72;
			if (nodeTypeValue === 'gpu') {
				max = 24;
			}
			$('.js-touchspin-dtaskspn').first().trigger('touchspin.updatesettings', {max: max});
		}
	}
	
	if ($('.js-select').length > 0) {
		$('.js-select').each(function(index, value) {
			$(value).select2();
		});
	}
	
	if ($('.js-touchspin').length > 0) {
		$('.js-touchspin').each(function(index, value) {
			let max = 16;
			if ($(value).data('max')) {
				max = parseInt($(value).data('max'));
			}
			$(value).TouchSpin({
				min: 1,
				max: max,
				step: 1,
				decimals: 0
			});
		});
	}
	
	let nodeTypeValue = null;
	if ($('.js-node-type').length > 0) {
		nodeTypeValue = $('.js-node-type').first().val();
		$('.js-node-type').change(function() {
			updateFieldsRelatedToNodeType($(this).val());
		});
	}
	
	if ($('.js-touchspin-ppn').length > 0) {
		let max = 36;
		if (nodeTypeValue === 'gpu') {
			max = 12;
		}
		$('.js-touchspin-ppn').first().TouchSpin({
			min: 1,
			max: max,
			step: 1,
			decimals: 0
		});
	}
	
	if ($('.js-touchspin-dtaskspn').length > 0) {
		let max = 72;
		if (nodeTypeValue === 'gpu') {
			max = 24;
		}
		$('.js-touchspin-dtaskspn').first().TouchSpin({
			min: 1,
			max: max,
			step: 1,
			decimals: 0
		});
	}
	
	if ($('.js-icheck').length > 0) {
		$('.js-icheck').each(function(index, value) {
			$(value).iCheck({
				checkboxClass: 'icheckbox icheckbox_square-grey',
				radioClass: 'iradio iradio_square-grey',
				increaseArea: '20%' // optional
			});
		});
	}
	
	if ($('.js-runtime-input-source').length > 0 &&
		$('.js-runtime-input-target').length > 0) {
		let $source = $('.js-runtime-input-source').first();
		let $target = $('.js-runtime-input-target').first();
		let runtime = $source.val();
		$target.val(runtime + ":00:00");
		$('.js-runtime-input-source').first().change(function() {
			let runtime = $(this).val();
			$target.val(runtime + ":00:00");
		});
	}

	if ($("#spawn_form").length > 0 &&
		$("#spawn_form button[type='submit']").length > 0) {
		let $form = $("#spawn_form").first();
		$form.submit(function() {
			$("#spawn_form button[type='submit']").first().prop('disabled',true);
			return true;
		});
	}

});
