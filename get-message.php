<?php
$req_admin = FALSE;
$get_json = FALSE;
require("access.php");
set_json();
if (!isset($_GET['id'])) {
	die_error(400, "Should have id!");
}
// TODO: Possibly limit this by instance? I dunno - does it really matter?
$post_id = intval($_GET['id']);
if ($user_admin) { // Show all posts to the administrator
	$query_input_text = "SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` , `RecipientID` FROM `Posts` LEFT JOIN `PostRecipients` ON ( `UID` = `PostID` ) WHERE `UID`=? AND ? = ?"; // UID, A, A - extra ?=? clause so that I can use the same binding for both queries.
} else {
	$query_input_text = "SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` , `RecipientID` FROM ( SELECT `UID` , `IsPublic` , `Title` , `Contents` , `Author` , `ResponseTo` , `Date` FROM `Posts` LEFT JOIN `PostRecipients` ON ( `PostID` = `UID` ) WHERE `UID`=? AND ( `IsPublic` = 1 OR `Author` = ? OR `RecipientID` = ? ) GROUP BY `UID` ) AS `Main` LEFT JOIN `PostRecipients` ON ( `UID` = `PostID` )"; // UID, user, user
}
$qry = $db->prepare($query_input_text);
if ($qry === FALSE || !$qry->bind_param("iii", $post_id, $user_uid, $user_uid) || !$qry->execute() || !$qry->bind_result($query_uid, $query_ispublic, $query_title, $query_data, $query_author, $query_responseto, $query_date, $query_recipient)) {
	die_error(500, "Server Error: Could not submit body query.");
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
if (count($posts) !== 1) {
	die_error(500, "Server Error: Post count assertion failed.");
}
echo json_encode($posts[0]);
