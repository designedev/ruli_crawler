루리웹 특정 게시판 내 글의 이미지를 저장하고 사용자별로 정리하는 코드.
이상한 짤들을 올리는 사람들이 보여서 특정 짤들을 올리는 사람, 빈도, 동일한 짤을 올리는 사람을 찾기 위해 만들게 됨..

일정 주기로 게시판의 글을 순회하면서, 마지막으로 체크한 시점 이후로 올라온 글들에 대해 짤을 저장하고, 게시자, 루리웹 아이디(고유 키), 이미지 경로와 크기 등을 저장한다.

