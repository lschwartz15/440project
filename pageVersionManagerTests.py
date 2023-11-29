import os
import unittest
import time

from Riki import create_app
from wiki.core import PageVersionManager


class TestPageVersionManager(unittest.TestCase):
	def setUp(self):
		self.app = create_app(os.getcwd())
		self.client = self.app.test_client()
		self.app.testing = True
		self.app.config['WTF_CSRF_ENABLED'] = False
		self.user = 'TEST'
		self.url = 'TESTPAGE'
		self.pvm = PageVersionManager(self.url, self.user)
		self.client.post('/user/login', data={'name': self.user, 'password': 'TEST'}, follow_redirects=True)

	def tearDown(self):
		self.client.get('/delete/' + self.url, follow_redirects=True)

	def get_page_data(self):
		with open(self.pvm.page_path, 'r', encoding='utf-8') as f:
			content = f.read().splitlines()
			title = content[0][7:]
			tags = content[1][6:]
			body = content[3]
			return title, tags, body

	def test_create_page(self):
		title = 'TEST_TITLE'
		tags = 'TEST'
		body = 'TEST_BODY'
		response = self.client.post('/edit/' + self.url,
									data={'title': title, 'body': body, 'tags': tags},
									follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(os.path.exists(self.pvm.page_path))
		self.assertTrue(os.path.exists(self.pvm.dir_path))
		self.assertTrue(os.path.exists(self.pvm.edits_path))
		self.assertTrue(os.path.exists(self.pvm.dir_path + '/' + self.pvm.get_timestamp().replace(':', ' ') + '.md'))
		edits = self.pvm.get_edits()
		self.assertEqual(len(edits), 1)
		page_title, page_tags, page_body = self.get_page_data()
		self.assertEqual(page_title, title)
		self.assertEqual(page_tags, tags)
		self.assertEqual(page_body, body)

	def test_update_page(self):
		title = 'TEST_TITLE'
		tags = 'TEST'
		body = 'TEST_BODY'
		title2 = 'TEST_TITLE2'
		tags2 = 'TEST2'
		body2 = 'TEST_BODY2'
		self.client.post('/edit/' + self.url,
									data={'title': title, 'body': body, 'tags': tags},
									follow_redirects=True)
		self.client.post('/user/login', data={'name': 'eric_jackman', 'password': 'pass'}, follow_redirects=True)
		time.sleep(1)
		response = self.client.post('/edit/' + self.url,
									data={'title': title2, 'body': body2, 'tags': tags2},
									follow_redirects=True)
		self.assertTrue(os.path.exists(self.pvm.dir_path + '/' + self.pvm.get_timestamp().replace(':', ' ') + '.md'))
		self.assertEqual(response.status_code, 200)
		edits = self.pvm.get_edits()
		self.assertEqual(len(edits), 2)
		page_title, page_tags, page_body = self.get_page_data()
		self.assertEqual(page_title, title2)
		self.assertEqual(page_tags, tags2)
		self.assertEqual(page_body, body2)

	def test_restore_page(self):
		title = 'TEST_TITLE'
		tags = 'TEST'
		body = 'TEST_BODY'
		title2 = 'TEST_TITLE2'
		tags2 = 'TEST2'
		body2 = 'TEST_BODY2'
		self.client.post('/edit/' + self.url,
									data={'title': title, 'body': body, 'tags': tags},
									follow_redirects=True)
		self.client.post('/user/login', data={'name': 'eric_jackman', 'password': 'pass'}, follow_redirects=True)
		time.sleep(1)
		response = self.client.post('/edit/' + self.url,
									data={'title': title2, 'body': body2, 'tags': tags2},
									follow_redirects=True)
		page_title, page_tags, page_body = self.get_page_data()
		self.assertEqual(page_title, title2)
		self.assertEqual(page_tags, tags2)
		self.assertEqual(page_body, body2)
		self.client.get('/edit/' + self.url + '/0', follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		page_title, page_tags, page_body = self.get_page_data()
		self.assertEqual(page_title, title)
		self.assertEqual(page_tags, tags)
		self.assertEqual(page_body, body)

	def test_delete_page(self):
		title = 'TEST_TITLE'
		tags = 'TEST'
		body = 'TEST_BODY'
		self.client.post('/edit/' + self.url,
									data={'title': title, 'body': body, 'tags': tags},
									follow_redirects=True)
		response = self.client.get('/delete/' + self.url, follow_redirects=True)
		self.assertEqual(response.status_code, 200)
		self.assertTrue(not os.path.exists(self.pvm.page_path))
		self.assertTrue(not os.path.exists(self.pvm.edits_path))
		self.assertTrue(not os.path.exists(self.pvm.dir_path))


if __name__ == '__main__':
	unittest.main()
