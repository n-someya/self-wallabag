<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use Wallabag\Entity\Entry;
use Wallabag\Entity\Tag;
use Wallabag\Entity\User;
use DateTime;

class ArticleEntityTest extends TestCase
{
    private $article;
    private $user;

    protected function setUp(): void
    {
        $this->user = new User();
        $this->user->setUsername('test_user');
        $this->user->setEmail('test@example.com');

        $this->article = new Entry($this->user);
    }

    public function testArticleCreation()
    {
        $this->assertInstanceOf(Entry::class, $this->article);
        $this->assertEquals($this->user, $this->article->getUser());
        $this->assertFalse($this->article->isArchived());
        $this->assertFalse($this->article->isStarred());
    }

    public function testArticleUrl()
    {
        $url = 'https://example.com/test-article';
        $this->article->setUrl($url);
        
        $this->assertEquals($url, $this->article->getUrl());
    }

    public function testArticleDomainName()
    {
        $url = 'https://example.com/test-article';
        $this->article->setUrl($url);
        $this->article->updateDomainName();
        
        $this->assertEquals('example.com', $this->article->getDomainName());
    }

    public function testArticleTitle()
    {
        $title = 'Test Article Title';
        $this->article->setTitle($title);
        
        $this->assertEquals($title, $this->article->getTitle());
    }

    public function testArticleContent()
    {
        $content = '<p>This is test content.</p>';
        $this->article->setContent($content);
        
        $this->assertEquals($content, $this->article->getContent());
    }

    public function testArticleReadingTime()
    {
        // Generate content with approximately 1000 words (about 5 minutes reading time)
        $content = str_repeat('Lorem ipsum dolor sit amet. ', 200);
        $this->article->setContent($content);
        
        // Update reading time
        $this->article->updateReadingTime();
        
        // Reading time should be greater than 0
        $this->assertGreaterThan(0, $this->article->getReadingTime());
    }

    public function testArticleArchiving()
    {
        // Initially not archived
        $this->assertFalse($this->article->isArchived());
        
        // Archive the article
        $this->article->setArchived(true);
        $this->assertTrue($this->article->isArchived());
        
        // Unarchive the article
        $this->article->setArchived(false);
        $this->assertFalse($this->article->isArchived());
    }

    public function testArticleStarring()
    {
        // Initially not starred
        $this->assertFalse($this->article->isStarred());
        
        // Star the article
        $this->article->setStarred(true);
        $this->assertTrue($this->article->isStarred());
        
        // Unstar the article
        $this->article->setStarred(false);
        $this->assertFalse($this->article->isStarred());
    }

    public function testArticleReadingStatus()
    {
        // Initially not read
        $this->assertNull($this->article->getReadAt());
        
        // Mark as read
        $now = new DateTime();
        $this->article->setReadAt($now);
        $this->assertEquals($now, $this->article->getReadAt());
        
        // Mark as unread
        $this->article->setReadAt(null);
        $this->assertNull($this->article->getReadAt());
    }

    public function testArticleTags()
    {
        // Initially no tags
        $this->assertCount(0, $this->article->getTags());
        
        // Create tags
        $tag1 = new Tag();
        $tag1->setLabel('test');
        
        $tag2 = new Tag();
        $tag2->setLabel('article');
        
        // Add tags to article
        $this->article->addTag($tag1);
        $this->article->addTag($tag2);
        
        // Check tags were added
        $this->assertCount(2, $this->article->getTags());
        $this->assertTrue($this->article->hasTag($tag1));
        $this->assertTrue($this->article->hasTag($tag2));
        
        // Remove a tag
        $this->article->removeTag($tag1);
        
        // Check tag was removed
        $this->assertCount(1, $this->article->getTags());
        $this->assertFalse($this->article->hasTag($tag1));
        $this->assertTrue($this->article->hasTag($tag2));
    }

    public function testArticleCreatedUpdatedDates()
    {
        $createdAt = new DateTime('2023-01-01');
        $this->article->setCreatedAt($createdAt);
        $this->assertEquals($createdAt, $this->article->getCreatedAt());
        
        $updatedAt = new DateTime('2023-01-02');
        $this->article->setUpdatedAt($updatedAt);
        $this->assertEquals($updatedAt, $this->article->getUpdatedAt());
    }

    public function testArticlePreviewPicture()
    {
        $previewUrl = 'https://example.com/image.jpg';
        $this->article->setPreviewPicture($previewUrl);
        
        $this->assertEquals($previewUrl, $this->article->getPreviewPicture());
    }

    public function testArticleMimeType()
    {
        $mimeType = 'text/html';
        $this->article->setMimetype($mimeType);
        
        $this->assertEquals($mimeType, $this->article->getMimetype());
    }

    public function testArticleLanguage()
    {
        $language = 'en';
        $this->article->setLanguage($language);
        
        $this->assertEquals($language, $this->article->getLanguage());
    }
}