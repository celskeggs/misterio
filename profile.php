<?php
$req_admin = FALSE;
$get_json = FALSE;
require("access.php");
set_json();
if (!isset($_GET['offset']) || !isset($_GET['limit']) || !isset($_GET['uid'])) {
	die_error(400, "Should have offset, limit, AND uid!");
}
$posts_offset = intval($_GET['offset']);
$posts_limit = intval($_GET['limit']);
$poster_uid = intval($_GET['uid']);
if ($user_admin) {
	$query_input_text = "SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` , `RecipientID` FROM ( SELECT `Instance` , `UID`, `IsPublic`, `Title`, `Contents`, `Author`, `ResponseTo`, `Date` FROM `Posts` LEFT JOIN `PostRecipients` ON `PostID`=`UID` WHERE (`RecipientID`=? OR `Author`=?)  GROUP BY `UID` ORDER BY `Date` LIMIT ? , ? ) AS `Main` LEFT JOIN `PostRecipients` ON ( `UID` = `PostID` ) WHERE `Instance` = ?";
	$double_target_id = true;
} else {
	$query_input_text = "SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` , `RecipientID` FROM ( SELECT `Instance` , `UID`, `IsPublic`, `Title`, `Contents`, `Author`, `ResponseTo`, `Date` FROM ( SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` FROM `Posts` LEFT JOIN `PostRecipients` ON ( `PostID` = `UID` ) WHERE ( `IsPublic` = 1 OR `Author` = ? OR `RecipientID` = ? ) GROUP BY `UID` ORDER BY `Date` ) AS `Base` LEFT JOIN `PostRecipients` ON `PostID`=`UID` WHERE (`RecipientID`=? OR `Author`=?) GROUP BY `UID` LIMIT ? , ? ) AS `Main` LEFT JOIN `PostRecipients` ON ( `UID` = `PostID` ) WHERE `Instance` = ?";
	$double_target_id = true;
}
$qry = $db->prepare($query_input_text);
if ($qry === FALSE) {
	die_error(500, "Server Error: Could not submit body query.");
}
if ($user_admin) {
	if ($double_target_id) {
		if (!$qry->bind_param("iiiii", $poster_uid, $poster_uid, $posts_offset, $posts_limit, $user_instance)) {
			die_error(500, "Server Error: Could not submit body query.");
		}
	} else {
		if (!$qry->bind_param("iiii", $poster_uid, $posts_offset, $posts_limit, $user_instance)) {
			die_error(500, "Server Error: Could not submit body query.");
		}
	}
} else {
	if ($double_target_id) {
		if (!$qry->bind_param("iiiiiii", $user_uid, $user_uid, $poster_uid, $poster_uid, $posts_offset, $posts_limit, $user_instance)) {
			die_error(500, "Server Error: Could not submit body query.");
		}
	} else {
		if (!$qry->bind_param("iiiiii", $user_uid, $user_uid, $poster_uid, $posts_offset, $posts_limit, $user_instance)) {
			die_error(500, "Server Error: Could not submit body query.");
		}
	}
}
if (!$qry->execute() || !$qry->bind_result($query_uid, $query_ispublic, $query_title, $query_data, $query_author, $query_responseto, $query_date, $query_recipient)) {
	die_error(500, "Server Error: Could not submit body query: " . $db->error);
}
$posts = array();
$uids = array();
while ($qry->fetch()) {
	$post_offset = array_search($query_uid, $uids, true);
	if ($post_offset !== false) {
		if ($query_recipient === null) {
			// Shouldn't happen - this should only be null if there are no recipients, which would mean that it should be the only entry, and $post_offset should be FALSE!
			die_error(500, "Recipient assertion failed");
		}
		$posts[$post_offset]['to'][] = $query_recipient;
		continue;
	}
	$recip = array();
	if ($query_recipient !== null) {
		$recip[] = $query_recipient;
	}
	$post = array('id' => $query_uid, 'public' => $query_ispublic ? true : false, 'title' => utf8_encode($query_title), 'data' => utf8_encode($query_data), 'from' => $query_author, 'prev' => $query_responseto, 'date' => strtotime($query_date) * 1000, 'to' => $recip);
	$posts[] = $post;
	$uids[] = $query_uid;
}
if (!$qry->close()) {
	die_error(500, "Server Error: Could not finish body query.");
}
echo json_encode(array('instance' => $user_instance, 'uid' => $user_uid, 'access' => $user_admin ? true : false, 'data' => $posts));
