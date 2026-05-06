// BY GOD'S GRACE ALONE

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SlitherTest {
    address public owner;
    uint256 public totalValue;
    mapping(address => uint256) public balances;

    constructor() {
        owner = msg.sender;
    }

    function deposit(uint256 amount) public payable {
        // Test basic require with message
        require(amount > 0, "Amount must be positive");
        require(msg.value == amount, "Incorrect ETH sent");

        balances[msg.sender] += amount;
        totalValue += amount;

        // Test assert for internal state consistency
        assert(totalValue >= amount);
    }

    function withdraw(uint256 amount) public {
        // Test state-based require
        require(balances[msg.sender] >= amount, "Insufficient balance");

        balances[msg.sender] -= amount;
        totalValue -= amount;

        payable(msg.sender).transfer(amount);
    }

    function updateOwner(address newOwner) public payable{
        // Test authorization require
        require(msg.sender == owner, "Only owner can call this");
        require(newOwner != address(0), "Invalid new owner address");
        
        owner = newOwner;
    }
}
