<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use Wallabag\Entity\User;
use Wallabag\Entity\Entry;
use DateTime;

class UserEntityTest extends TestCase
{
    private $user;

    protected function setUp(): void
    {
        $this->user = new User();
    }

    public function testUserCreation()
    {
        $this->assertInstanceOf(User::class, $this->user);
        $this->assertTrue($this->user->isEnabled());
    }

    public function testUsername()
    {
        $username = 'test_user';
        $this->user->setUsername($username);
        
        $this->assertEquals($username, $this->user->getUsername());
    }

    public function testEmail()
    {
        $email = 'test@example.com';
        $this->user->setEmail($email);
        
        $this->assertEquals($email, $this->user->getEmail());
        $this->assertEquals($email, $this->user->getUserIdentifier());
    }

    public function testPassword()
    {
        $plainPassword = 'test_password';
        $encodedPassword = password_hash($plainPassword, PASSWORD_BCRYPT);
        
        // Set encoded password
        $this->user->setPassword($encodedPassword);
        
        // Password should be stored as the encoded version
        $this->assertEquals($encodedPassword, $this->user->getPassword());
        
        // Plain password should be null
        $this->assertNull($this->user->getPlainPassword());
        
        // Set plain password
        $this->user->setPlainPassword($plainPassword);
        
        // Plain password should be accessible
        $this->assertEquals($plainPassword, $this->user->getPlainPassword());
    }

    public function testRoles()
    {
        // Default roles should include ROLE_USER
        $this->assertContains('ROLE_USER', $this->user->getRoles());
        
        // Add admin role
        $this->user->addRole('ROLE_ADMIN');
        $this->assertContains('ROLE_ADMIN', $this->user->getRoles());
        
        // Remove admin role
        $this->user->removeRole('ROLE_ADMIN');
        $this->assertNotContains('ROLE_ADMIN', $this->user->getRoles());
        
        // Cannot remove ROLE_USER
        $this->user->removeRole('ROLE_USER');
        $this->assertContains('ROLE_USER', $this->user->getRoles());
    }

    public function testUserEntries()
    {
        // Initially no entries
        $this->assertCount(0, $this->user->getEntries());
        
        // Create entry
        $entry = new Entry($this->user);
        $entry->setUrl('https://example.com/test');
        $entry->setTitle('Test Entry');
        
        // Add entry to user
        $this->user->addEntry($entry);
        
        // Check entry was added
        $this->assertCount(1, $this->user->getEntries());
        
        // Remove entry
        $this->user->removeEntry($entry);
        
        // Check entry was removed
        $this->assertCount(0, $this->user->getEntries());
    }

    public function testUserCreatedAt()
    {
        $date = new DateTime('2023-01-01');
        $this->user->setCreatedAt($date);
        
        $this->assertEquals($date, $this->user->getCreatedAt());
    }

    public function testUserUpdatedAt()
    {
        $date = new DateTime('2023-01-01');
        $this->user->setUpdatedAt($date);
        
        $this->assertEquals($date, $this->user->getUpdatedAt());
    }

    public function testUserLastLogin()
    {
        // Initially null
        $this->assertNull($this->user->getLastLogin());
        
        // Set last login
        $date = new DateTime('2023-01-01');
        $this->user->setLastLogin($date);
        
        $this->assertEquals($date, $this->user->getLastLogin());
    }

    public function testUserEnabled()
    {
        // Initially enabled
        $this->assertTrue($this->user->isEnabled());
        
        // Disable user
        $this->user->setEnabled(false);
        $this->assertFalse($this->user->isEnabled());
        
        // Enable user
        $this->user->setEnabled(true);
        $this->assertTrue($this->user->isEnabled());
    }

    public function testUserConfig()
    {
        // Set config
        $config = ['theme' => 'dark', 'items_per_page' => 30];
        $this->user->setConfig($config);
        
        $this->assertEquals($config, $this->user->getConfig());
        
        // Get specific config value
        $this->assertEquals('dark', $this->user->getConfigByKey('theme'));
        $this->assertEquals(30, $this->user->getConfigByKey('items_per_page'));
        
        // Default value for non-existent key
        $this->assertEquals('default', $this->user->getConfigByKey('non_existent', 'default'));
    }

    public function testUserName()
    {
        // Test full name generation
        $this->user->setName('John');
        $this->assertEquals('John', $this->user->getName());
        
        // Default to username if name not set
        $this->user->setName(null);
        $this->user->setUsername('john_doe');
        $this->assertEquals('john_doe', $this->user->getName());
    }

    public function testEraseCredentials()
    {
        // Set plain password
        $this->user->setPlainPassword('test_password');
        $this->assertEquals('test_password', $this->user->getPlainPassword());
        
        // Erase credentials should clear plain password
        $this->user->eraseCredentials();
        $this->assertNull($this->user->getPlainPassword());
    }
}