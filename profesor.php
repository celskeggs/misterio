<?php
error_reporting(E_ALL);
ini_set("display_errors", "stdout");
$req_access = 2;
require('begin.php');
function generate_token() {
	return sha1(microtime(true).mt_rand(10000,90000).sha1(uniqid()));
}
if (isset($_GET['mod'])) {
	$mod_op = $_GET['mod'];
	$mod_msg = "Unknown Operation: $mod_op";
	if ($mod_op === "user") {
		if (isset($_POST['uid']) && isset($_POST['name']) && isset($_POST['email'])
                 && $_POST['uid'] !== "" && $_POST['name'] !== "" && isset($_POST['avatar']) && $_POST['avatar'] !== "") {
			$uid = intval($_POST['uid']);
			$name = $_POST['name'];
			$email = $_POST['email'];
			$admin = (isset($_POST['admin']) && $_POST['admin'] === "on") ? 1 : 0;
			$avatar = $_POST['avatar'];
			$qry = $db->prepare("SELECT `Name`, `Email`, `Admin`, `Avatar` FROM `Players` WHERE `UID`=?");
			$qry->bind_param("i", $uid);
			$qry->execute();
			$qry->bind_result($query_name, $q_email, $query_admin, $query_avatar);
			if (!$qry->fetch()) {
				$mod_msg = "No such user!";
				$qry->close();
			} else {
				$query_email = ($q_email === null) ? "" : $q_email;
				if ($email === $query_email && $name === $query_name && $admin === $query_admin && $avatar == $query_avatar) {
					$mod_msg = "No modification.";
					$qry->close();
				} else {
					$qry->close();
					$mod_msg = "User modified!";
					$qtok = "";
					if ($email !== $query_email) {
						if ($query_email !== "") {
							$mod_msg = "User modified & email sent!";
							$qbdy = "Hola!\n";
							$qbdy .= "Tu cuenta del Misterio de Cuzco no es tuyo no más.\n";
							$qbdy .= "Si piensas que esto es en error, por favor contactas a tu profesor.";
							mail($query_email, "Tu cuenta del Misterio de Cuzco", $qbdy);
						}
						if ($email !== "") {
							$qtok = generate_token();
							$mod_msg = "User modified & email sent!";
							$qbdy = "Hola!\n";
							$qbdy .= "Una cuenta del Misterio de Cuzces tuyo ahora.\n";
							$qbdy .= "Puedes entrar en Misterio de Cuzco con este enlace: $redir_url/login.php?token=$qtok\n";
							$qbdy .= "Si piensas que esto es en error, por favor contactas a tu profesor.";
							mail($email, "Tu cuenta del Misterio de Cuzco", $qbdy);
						}
					} else if ($email !== "") {
						if ($name !== $query_name) {
							$mod_msg = "User modified & email sent!";
							$qbdy = "Hola!\n";
							$qbdy .= "Tu cuenta del Misterio de Cuzces tiene un nombre nuevo: $name!\n";
							$qbdy .= "Si piensas que esto es en error, por favor contactas a tu profesor.";
							mail($query_email, "Tu cuenta del Misterio de Cuzco", $qbdy);
						}
					}
					if ($email === "") {
						$mqry = $db->prepare("UPDATE `Players` SET `Name`=?, `Token`=NULL, `Email`=NULL, `Admin`=?, `Avatar`=? WHERE `UID`=?");
						$mqry->bind_param("sisi", $name, $admin, $avatar, $uid);
					} else if ($qtok !== "") {
						$mqry = $db->prepare("UPDATE `Players` SET `Name`=?, `Token`=?, `Email`=?, `Admin`=?, `Avatar`=? WHERE `UID`=?");
						$mqry->bind_param("sssisi", $name, $qtok, $email, $admin, $avatar, $uid);
					} else {
						$mqry = $db->prepare("UPDATE `Players` SET `Name`=?, `Email`=?, `Admin`=?, `Avatar`=? WHERE `UID`=?");
						$mqry->bind_param("ssisi", $name, $email, $admin, $avatar, $uid);
					}
					$mqry->execute();
					$mqry->close();
				}
			}
		} else {
			$mod_msg = "Bad request.";
		}
	} else if ($mod_op === "useradd") {
		if (isset($_POST['name']) && $_POST['name'] !== ""
                 && isset($_POST['avatar']) && $_POST['avatar'] !== "") {
			$name = $_POST['name'];
			$email = isset($_POST['email']) ? $_POST['email'] : "";
			$avatar = $_POST['avatar'];
			if ($email !== "" && strpos($email, "@") === FALSE) {
				$mod_msg = "Invalid email!";
			} else {
				$admin = (isset($_POST['admin']) && $_POST['admin'] === "on") ? 1 : 0;
				if ($email === "") {
					$mqry = $db->prepare("INSERT INTO `Players` (`Name`,`Admin`,`Avatar`) VALUES (?, ?, ?)");
					$mqry->bind_param("sis", $name, $admin, $avatar);
					$mqry->execute();
					$mqry->close();
					$mod_msg = "User added.";
				} else {
					$mqry = $db->prepare("INSERT INTO `Players` (`Name`,`Token`,`Email`,`Admin`,`Avatar`) VALUES (?, ?, ?, ?, ?)");
					$qtok = generate_token();
					$mqry->bind_param("sssis", $name, $qtok, $email, $admin, $avatar);
					$mqry->execute();
					$mqry->close();
					$emsg = "Hola!\n";
					$emsg .= "Tu nombre en Misterio de Cuzco es $name.\n";
					$emsg .= "Puedes entrar en Misterio de Cuzco con este enlace: $redir_url/login.php?token=$qtok\n" ;
					$emsg .= "Si tienes preguntas, por favor contactas a tu profesor de Españl.\n";
					mail($email, "Tu cuenta del Misterio de Cuzco", $emsg);
					$mod_msg = "User added & email sent.";
				}
			}
		} else {
			$mod_msg = "Bad request";
		}
	} else if ($mod_op === "userdel") {
		if (isset($_POST['uid']) && $_POST['uid'] !== "") {
			$uid = intval($_POST['uid']);
			$qry = $db->prepare("SELECT `Email`,`Name` FROM `Players` WHERE `UID`=?");
			$qry->bind_param('i', $uid);
			$qry->execute();
			$qry->bind_result($query_email, $query_name);
			if (!$qry->fetch()) {
				$mod_msg = "Could not find user!";
				$qry->close();
			} else {
				$email_tgt = $query_email;
				$name_tgt = $query_name;
				$qry->close();
				if ($email_tgt !== null && $email_tgt !== "") {
					$ebdy = "Hola!\n";
					$ebdy .= "Tu cuenta del Misterio de Cuzco con el nombre \"$name_tgt\" es borrado.\n";
					$ebdy .= "Si piensas que esto es en error, por favor contactas a tu profesor.";
					mail($email_tgt, "Tu cuenta del Misterio de Cuzco", $ebdy);
				}
				$mqry = $db->prepare("DELETE FROM `Players` WHERE `UID`=?");
				$mqry->bind_param('i', $uid);
				$mqry->execute();
				$mqry->close();
			}
			$mod_msg = "Deleted user.";
		} else {
			$mod_msg = "Bad request.";
		}
	}
	redirect("profesor.php?msg=" . urlencode($mod_msg));
}
$title = "Profesor";
require('header.php');
?>
<div id="title">
La pachina de Profesor. <a href='index.php'>Revolver</a>
</div>
<div id="content">
<div class="profesor-label">Personas</div>
<table id="table-users" border="1">
<tr><td>UID</td><td>Name</td><td>Email</td><td>Admin</td><td>Token</td><td>Avatar</td><td>Modify</td><td>Remove</td></tr>
<?php
$qry = $db->prepare("SELECT `UID`, `Name`, `Email`, `Admin`, `Token`, `Avatar` FROM `Players`");
$qry->execute();
$qry->bind_result($qry_uid, $qry_name, $qry_email, $qry_admin, $qry_token, $qry_avatar);
$avatars = array();
while ($qry->fetch()) {
	echo "<tr>";
	echo "<form action='profesor.php?mod=user' method='POST'>";
	echo "<td><input type='hidden' name='uid' value='" . htmlentities("$qry_uid") . "'>" . htmlentities("$qry_uid") . "</td>";
	echo "<td><input type='text' name='name' value='" . htmlentities($qry_name) . "' /></td>";
	echo "<td><input type='text' name='email' value='" . htmlentities($qry_email) . "' /></td>";
	echo "<td><input type='checkbox' name='admin'" . ($qry_admin ? " checked='on' " : " ") . "/></td>";
	echo "<td>" . htmlentities("$qry_token") . "</td>";
	$avatar = str_replace("'", urlencode("'"), str_replace('"', urlencode('"'), $qry_avatar));
	if (!in_array($avatar, $avatars)) {
		$avatars[] = $avatar;
	}
	echo "<td><input type='text' name='avatar' value='" . htmlentities("$qry_avatar") . "' /></td>";
	echo "<td><input type='submit' value='Modify'></td>";
	echo "</form>";
	echo "<form action='profesor.php?mod=userdel' method='POST'>";
	if ($qry_admin) {
		echo "<td></td>";
	} else {
		echo "<td><input type='hidden' name='uid' value='" . htmlentities("$qry_uid") . "'><input type='submit' value='Delete'></td>";
	}
	echo "</form>";
	echo "</tr>";
}
?>
<tr><form action='profesor.php?mod=useradd' method='POST'><td></td><td><input type='text' name='name'></td><td><input type='text' name='email'></td><td><input type='checkbox' name='admin'></td><td>[Autogenerated]</td><td><input type='text' name='avatar' value='placeholder.png' /></td><td><input type='submit' value='Add'></td></form><td></td></tr>
<tr><td>UID</td><td>Name</td><td>Email</td><td>Admin</td><td>Token</td><td>Avatar</td><td>Modify</td><td>Remove</td></tr>
</table>

</div>
<?php
require('footer.php');
?>
