function submit_registration() {
  var valid = validate_registration();
  if (valid) {
    var pass = document.getElementById('password1').value;
    var email = document.getElementById('email').value;
    scrypt(pass, (email + 'xyz').substring(0, 8), {
      N: 4,
      r: 4,
      p: 2,
      dkLen: 16,
      encoding: 'hex'
    }, function(hash) {
      document.getElementById('pass_hash').value = hash;
    // document.getElementById('registration-form').submit(); //form submission
    });
  }

  console.log('submit_registration returned ' + valid);

  return valid;
}

function validate_registration() {
  var err_count = 0;
  if (!validate_email()) err_count++;
  if (!validate_first_name()) err_count++;
  if (!validate_last_name()) err_count++;
  if (!validate_password1()) err_count++;
  if (!validate_password2()) err_count++;

  return err_count == 0;
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

function validate_first_name() {
  var first_name = document.getElementById('first_name');
  var first_name_error = document.getElementById('first_name-error');
  if (first_name.value.length == 0) {
    first_name_error.innerText = 'First name is required.';
    first_name_error.style.display = 'block';
    return false;
  } else {
    first_name_error.style.display = 'none';
    return true;
  }
}

function validate_last_name() {
  var last_name = document.getElementById('last_name');
  var last_name_error = document.getElementById('last_name-error');
  if (last_name.value.length == 0) {
    last_name_error.innerText = 'Last name is required.';
    last_name_error.style.display = 'block';
    return false;
  } else {
    last_name_error.style.display = 'none';
    return true;
  }
}

function validate_password1() {
  var password1 = document.getElementById('password1');
  var password1_error = document.getElementById('password1-error');
  if (password1.value.length < 6 || password1.value.length > 12) {
    password1_error.innerText = 'Password must be between 6 and 12 characters.';
    password1_error.style.display = 'block';
    return false;
  } else {
    password1_error.style.display = 'none';
    return true;
  }
}

function validate_password2() {
  var password1 = document.getElementById('password1');
  var password2 = document.getElementById('password2');
  var password2_error = document.getElementById('password2-error');
  if (password2.value != password1.value) {
    password2_error.innerText = 'Passwords must match.';
    password2_error.style.display = 'block';
    return false;
  } else {
    password2_error.style.display = 'none';
    return true;
  }
}
