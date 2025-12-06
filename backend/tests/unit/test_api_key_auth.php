<?php

namespace Tests\Unit;

use PHPUnit\Framework\TestCase;
use Wallabag\Entity\User;
use Wallabag\Entity\ApiKey;
use DateTime;

class ApiKeyAuthTest extends TestCase
{
    private $apiKey;
    private $user;

    protected function setUp(): void
    {
        $this->user = new User();
        $this->user->setUsername('test_user');
        $this->user->setEmail('test@example.com');
        
        $this->apiKey = new ApiKey($this->user);
    }

    public function testApiKeyCreation()
    {
        $this->assertInstanceOf(ApiKey::class, $this->apiKey);
        $this->assertEquals($this->user, $this->apiKey->getUser());
        $this->assertTrue($this->apiKey->isActive());
        $this->assertNull($this->apiKey->getExpiresAt());
    }

    public function testApiKeyValue()
    {
        $keyValue = 'test_api_key_' . bin2hex(random_bytes(16));
        $this->apiKey->setKey($keyValue);
        
        // Key value should be hashed, not stored in plain text
        $this->assertNotEquals($keyValue, $this->apiKey->getKey());
        
        // Verify key validates correctly
        $this->assertTrue($this->apiKey->validateKey($keyValue));
        $this->assertFalse($this->apiKey->validateKey('wrong_key'));
    }

    public function testApiKeyName()
    {
        $name = 'Test API Key';
        $this->apiKey->setName($name);
        
        $this->assertEquals($name, $this->apiKey->getName());
    }

    public function testApiKeyCreatedAt()
    {
        $date = new DateTime('2023-01-01');
        $this->apiKey->setCreatedAt($date);
        
        $this->assertEquals($date, $this->apiKey->getCreatedAt());
    }

    public function testApiKeyExpiration()
    {
        // Initially not expired
        $this->assertFalse($this->apiKey->isExpired());
        
        // Set expiration in the future
        $future = new DateTime('+7 days');
        $this->apiKey->setExpiresAt($future);
        
        $this->assertEquals($future, $this->apiKey->getExpiresAt());
        $this->assertFalse($this->apiKey->isExpired());
        
        // Set expiration in the past
        $past = new DateTime('-1 day');
        $this->apiKey->setExpiresAt($past);
        
        $this->assertTrue($this->apiKey->isExpired());
        
        // Remove expiration
        $this->apiKey->setExpiresAt(null);
        $this->assertFalse($this->apiKey->isExpired());
    }

    public function testApiKeyActive()
    {
        // Initially active
        $this->assertTrue($this->apiKey->isActive());
        
        // Deactivate
        $this->apiKey->setActive(false);
        $this->assertFalse($this->apiKey->isActive());
        
        // Reactivate
        $this->apiKey->setActive(true);
        $this->assertTrue($this->apiKey->isActive());
    }

    public function testApiKeyLastUsedAt()
    {
        // Initially null
        $this->assertNull($this->apiKey->getLastUsedAt());
        
        // Set last used
        $date = new DateTime('2023-01-01');
        $this->apiKey->setLastUsedAt($date);
        
        $this->assertEquals($date, $this->apiKey->getLastUsedAt());
    }

    public function testApiKeyValidation()
    {
        $keyValue = 'test_api_key_' . bin2hex(random_bytes(16));
        $this->apiKey->setKey($keyValue);
        
        // Valid key, active, not expired
        $this->assertTrue($this->apiKey->isValid($keyValue));
        
        // Wrong key
        $this->assertFalse($this->apiKey->isValid('wrong_key'));
        
        // Inactive key
        $this->apiKey->setActive(false);
        $this->assertFalse($this->apiKey->isValid($keyValue));
        $this->apiKey->setActive(true);
        
        // Expired key
        $past = new DateTime('-1 day');
        $this->apiKey->setExpiresAt($past);
        $this->assertFalse($this->apiKey->isValid($keyValue));
    }

    public function testApiKeyRenewal()
    {
        // Set initial expiration
        $initialExpiry = new DateTime('+30 days');
        $this->apiKey->setExpiresAt($initialExpiry);
        
        // Renew for another 60 days
        $this->apiKey->renew(60);
        
        // Expiry should be at least 60 days from now
        $minExpiry = new DateTime('+59 days');
        $this->assertGreaterThan($minExpiry, $this->apiKey->getExpiresAt());
        
        // Renew with no expiration
        $this->apiKey->renew(null);
        $this->assertNull($this->apiKey->getExpiresAt());
    }

    public function testApiKeyRevocation()
    {
        // Initially active
        $this->assertTrue($this->apiKey->isActive());
        
        // Revoke
        $this->apiKey->revoke();
        
        // Should be inactive after revocation
        $this->assertFalse($this->apiKey->isActive());
    }

    public function testApiKeyUsage()
    {
        // Initially null last used timestamp
        $this->assertNull($this->apiKey->getLastUsedAt());
        
        // Record usage
        $this->apiKey->recordUsage();
        
        // Last used should be set to current time
        $now = new DateTime();
        $lastUsed = $this->apiKey->getLastUsedAt();
        
        $this->assertNotNull($lastUsed);
        
        // Should be within a few seconds of now
        $diff = $now->getTimestamp() - $lastUsed->getTimestamp();
        $this->assertLessThan(5, abs($diff));
    }
}