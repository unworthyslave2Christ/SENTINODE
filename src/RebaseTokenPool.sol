// // BY GOD'S GRACE ALONE

// // Layout of Contract:
// // version
// // imports
// // errors
// // interfaces, libraries, contracts
// // Type declarations
// // State variables
// // Events
// // Modifiers
// // Functions

// // Layout of Functions:
// // constructor
// // receive function (if exists)
// // fallback function (if exists)
// // external
// // public
// // internal
// // private
// // internal & private view & pure functions
// // external & public view & pure functions

// //SPDX-License-Identifier: MIT
// pragma solidity ^0.8.24;

// import {TokenPool} from "@ccip/contracts/pools/TokenPool.sol";
// import {Pool} from "@ccip/contracts/libraries/Pool.sol";


// contract RebaseTokenPool is TokenPool{

//     // State variables
//     uint8 private constant LOCAL_TOKEN_DECIMALS_OR_PRECISION = 18;

//     constructor(
//         IERC20 _token, 
//         address[] memory _allowList,
//         address _rmnProxy,
//         address _router
//     ) TokenPool(
//         _token,
//         LOCAL_TOKEN_DECIMALS_OR_PRECISION,
//         _allowList,
//         _rmnProxy,
//         _router
//     ) {}


//     function lockOrBurn(
//         Pool.LockOrBurnInV1 calldata lockOrBurnIn
//     ) external returns (Pool.LockOrBurnOutV1 memory lockOrBurnOut){
//         _validateLockOrBurn(lockOrBurnIn);
//     }

//     function releaseOrMint(
//         Pool.ReleaseOrMintInV1 calldata releaseOrMintIn
//     ) external returns (Pool.ReleaseOrMintOutV1 memory){

//     }


// }

