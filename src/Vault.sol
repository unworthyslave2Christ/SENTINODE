// BY GOD'S GRACE ALONE

// Layout of Contract:
// version
// imports
// errors
// interfaces, libraries, contracts
// Type declarations
// State variables
// Events
// Modifiers
// Functions

// Layout of Functions:
// constructor
// receive function (if exists)
// fallback function (if exists)
// external
// public
// internal
// private
// internal & private view & pure functions
// external & public view & pure functions

// SPDX-License-Identifier:MIT
pragma solidity ^0.8.24;

// Imports
import {IRebaseToken} from "./interfaces/IRebaseToken.sol";

error Vault__RedeemFailed();


contract Vault {
    IRebaseToken private immutable i_rebaseToken;

    event Deposit(address indexed user, uint256 amount);
    event Redeem(address indexed user, uint256 amount);

    constructor(IRebaseToken _rebaseToken){
        i_rebaseToken = _rebaseToken;
    }

    receive() external payable {}

    fallback() external payable {}

    /**
     * @notice Allows users to deposit and mint rebase tokens in return
     */
    function deposit() external payable {
        // we need to use the amount of ETH the user has sent to mint tokens to the user
        i_rebaseToken.mint(msg.sender, msg.value);
        emit Deposit(msg.sender, msg.value);
    }


    /**
     * @notice Allows users to redeem their rebase tokens for ETH
     * @param _amount The amount of rebase-tokens-equivalent ETH to redeem 
     */
    function redeem(uint256 _amount) external {
        if (_amount >= type(uint256).max){
            _amount = i_rebaseToken.balanceOf(msg.sender);
        }
        // 1. Burn the given amount of tokens already minted to the user
        i_rebaseToken.burn(msg.sender, _amount);
        // 2. Send back to the user an equivalent amount of their locked ETH 
        (bool success,) = payable(msg.sender).call{value: _amount}("");
        if (!success){
            revert Vault__RedeemFailed();
        }
        emit Redeem(msg.sender, _amount);
    }



    /**
     * @notice Get the address of the rebase token
     * @return The address of the rebase token
     */
    function getRebaseTokenAddress() external view returns (address){
        return address(i_rebaseToken);
    }



}