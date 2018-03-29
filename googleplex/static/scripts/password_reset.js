function request_reset() {
  var valid = validate_email();
  if (valid) {
    document.getElementById('request-reset-form').submit(); //form submission
  }

  console.log('submit_registration returned ' + valid);

  return valid;
}

function validate_email() {
  var email = document.getElementById('email');
  var email_error = document.getElementById('email-error');
  if (email.value.length == 0) {
    email_error.innerText = 'Email is required.';
    email_error.style.display = 'block';
    return false;
  } else {
    email_error.style.display = 'none';
    return true;
  }
}

function validate(input) {
  if (input.value != document.getElementById('new_pass_1').value) {
    input.setCustomValidity('Password Must be Matching.');
  } else {
    // input is valid -- reset the error message
    input.setCustomValidity('');
  }
}

function submit_reset() {
  var new_pass = document.getElementById('new_pass_1').value;
  var email = document.getElementById('user_email').value;

  scrypt(new_pass, (email + 'xyz').substring(0, 8), {
    N: 4,
    r: 4,
    p: 2,
    dkLen: 16,
    encoding: 'hex'
  }, function(new_pass_hash) {
    document.getElementById('new_pass_hash').value = new_pass_hash;

    document.getElementById('password-reset-form').submit(); //form submission
  });
}
